"""Feed sync: CISA KEV (csv), FIRST EPSS (csv.gz), NVD recent (json), CWE names (xml zip).
All best-effort with per-feed error capture; parsers unit-testable offline."""
import csv
import gzip
import io
import json
import os
import time
import urllib.request
import zipfile

from . import db
from .score import lab_map, priority, severity_of

UA = {"User-Agent": "kingaweb-security-lab-intel/0.1 (+training-platform)"}
KEV_URL = "https://www.cisa.gov/sites/default/files/csv/known_exploited_vulnerabilities.csv"
EPSS_URL = "https://epss.cyentia.com/epss_scores-current.csv.gz"
NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
CWE_URL = "https://cwe.mitre.org/data/xml/cwec_latest.xml.zip"

def fetch(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def sync_kev(raw: bytes | None = None) -> dict:
    t0, n = time.time(), 0
    try:
        data = raw if raw is not None else fetch(KEV_URL)
        for row in csv.DictReader(io.StringIO(data.decode("utf-8", "replace"))):
            cve = (row.get("cveID") or "").strip()
            if not cve:
                continue
            db.upsert_vuln({"cve": cve, "kev": True,
                            "priority": priority(0, True, 0, lab_map().get(cve, [])),
                            "labs": json.dumps(lab_map().get(cve, []))}, reason="kev-sync")
            n += 1
        return {"feed": "kev", "records": n, "seconds": round(time.time() - t0, 1)}
    except Exception as e:
        return {"feed": "kev", "records": n, "error": f"{type(e).__name__}: {e}"}

def sync_epss(raw: bytes | None = None, max_rows: int = 0) -> dict:
    t0, n = time.time(), 0
    try:
        data = raw if raw is not None else fetch(EPSS_URL, timeout=120)
        if data[:2] == b"\x1f\x8b":
            data = gzip.decompress(data)
        lines = data.decode("utf-8", "replace").splitlines()
        start = next((i for i, l in enumerate(lines[:5]) if l.startswith("cve,")), 0)
        for row in csv.DictReader(lines[start:]):
            cve = (row.get("cve") or "").strip()
            try:
                epss = float(row.get("epss") or 0)
            except ValueError:
                continue
            if not cve:
                continue
            c = db.conn()
            try:
                old = c.execute("SELECT cvss, kev FROM vulns WHERE cve=?", (cve,)).fetchone()
                if old:
                    labs = json.loads((c.execute("SELECT labs FROM vulns WHERE cve=?", (cve,)).fetchone() or ["[]"])[0])
                    c.execute("UPDATE vulns SET epss=?, priority=?, updated_at=? WHERE cve=?",
                              (epss, priority(old["cvss"], bool(old["kev"]), epss, labs), time.time(), cve))
                    c.commit()
                else:
                    db.upsert_vuln({"cve": cve, "epss": epss,
                                    "priority": priority(0, False, epss, lab_map().get(cve, [])),
                                    "labs": json.dumps(lab_map().get(cve, []))}, reason="epss-sync")
                n += 1
            finally:
                c.close()
            if max_rows and n >= max_rows:
                break
        return {"feed": "epss", "records": n, "seconds": round(time.time() - t0, 1)}
    except Exception as e:
        return {"feed": "epss", "records": n, "error": f"{type(e).__name__}: {e}"}

def _cvss_of(vuln: dict) -> tuple[float, str]:
    best, sev = 0.0, "none"
    for m in vuln.get("metrics", {}).get("cvssMetricV31", []) + vuln.get("metrics", {}).get("cvssMetricV30", []):
        d = m.get("cvssData", {})
        if float(d.get("baseScore", 0)) >= best:
            best, sev = float(d["baseScore"]), d.get("baseSeverity", "high").lower()
    if not best:
        for m in vuln.get("metrics", {}).get("cvssMetricV2", []):
            d = m.get("cvssData", {})
            if float(d.get("baseScore", 0)) >= best:
                best = float(d["baseScore"])
        sev = severity_of(best)
    return best, sev

def sync_nvd(raw: bytes | None = None, limit: int = 20) -> dict:
    t0, n = time.time(), 0
    try:
        if raw is None:
            url = f"{NVD_URL}?resultsPerPage={limit}&orderby=lastMod&order=desc"
            try:
                data = fetch(url)
            except Exception:
                url = f"{NVD_URL}?resultsPerPage={limit}"
                data = fetch(url)
        else:
            data = raw
        for item in json.loads(data).get("vulnerabilities", [])[:limit]:
            v = item.get("cve", {})
            cve = v.get("id", "")
            if not cve:
                continue
            cvss, sev = _cvss_of(v)
            desc = next((d.get("value", "") for d in v.get("descriptions", []) if d.get("lang") == "en"), "")
            c = db.conn()
            try:
                old = c.execute("SELECT kev, epss FROM vulns WHERE cve=?", (cve,)).fetchone()
                kev = bool(old["kev"]) if old else False
                epss = old["epss"] if old else 0
                labs = lab_map().get(cve, [])
                db.upsert_vuln({"cve": cve, "published": v.get("published", ""), "modified": v.get("lastModified", ""),
                                "cvss": cvss, "severity": sev, "description": desc, "kev": kev, "epss": epss,
                                "priority": priority(cvss, kev, epss, labs), "labs": json.dumps(labs)},
                               reason="nvd-sync")
                n += 1
            finally:
                c.close()
        return {"feed": "nvd", "records": n, "seconds": round(time.time() - t0, 1)}
    except Exception as e:
        return {"feed": "nvd", "records": n, "error": f"{type(e).__name__}: {e}"}

def cwe_names(raw: bytes | None = None, limit: int = 2000) -> dict:
    """id -> name for CWE weaknesses (used by finding/report CWE hints)."""
    import xml.etree.ElementTree as ET
    try:
        data = raw if raw is not None else fetch(CWE_URL, timeout=120)
        zf = zipfile.ZipFile(io.BytesIO(data))
        xml_name = next(n for n in zf.namelist() if n.endswith(".xml"))
        root = ET.fromstring(zf.read(xml_name))
        ns = {"c": "http://cwe.mitre.org/cwe-7"}
        out = {}
        for w in root.findall(".//c:Weakness", ns)[:limit]:
            out[w.get("ID", "")] = w.get("Name", "")
        return out
    except Exception:
        return {}

def sync_all() -> dict:
    max_epss = int(os.environ.get("INTEL_MAX_EPSS_ROWS", "0") or 0)
    nvd_limit = int(os.environ.get("INTEL_NVD_LIMIT", "20") or 20)
    out = {"started": time.time(), "feeds": {}}
    c = db.conn()
    try:
        for name, fn in (("kev", lambda: sync_kev()),
                         ("epss", lambda: sync_epss(max_rows=max_epss)),
                         ("nvd", lambda: sync_nvd(limit=nvd_limit))):
            t0 = time.time()
            res = fn()
            c.execute("INSERT INTO sync_runs(feed,started,finished,records,error) VALUES(?,?,?,?,?)",
                      (name, t0, time.time(), res.get("records", 0), res.get("error", "")))
            c.commit()
            out["feeds"][name] = res
    finally:
        c.close()
    out["finished"] = time.time()
    return out
