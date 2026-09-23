"""Unit tests: scoring, history/queue semantics, feed parsers (offline fixtures)."""
import os
os.environ["INTEL_DB"] = "/tmp/opencode-intel-test.db"
if os.path.exists("/tmp/opencode-intel-test.db"):
    os.remove("/tmp/opencode-intel-test.db")

from fastapi.testclient import TestClient
from app import db, score
from app.main import app
from app import sync as syncmod

db.init()
c = TestClient(app, raise_server_exceptions=False)
H = {"Authorization": "Bearer dev-intel-token"}

def test_priority_orders_kev_and_epss():
    assert score.priority(7.5, True, 0.9, []) > score.priority(9.8, False, 0.0, [])
    assert score.priority(5.0, False, 0.0, ["web-xss-01"]) > score.priority(5.0, False, 0.0, [])
    assert score.severity_of(9.1) == "critical" and score.severity_of(0) == "none"

def test_history_and_queue_on_change():
    db.upsert_vuln({"cve": "CVE-TEST-1", "cvss": 5.0, "severity": "medium", "priority": 5.0}, reason="t")
    db.upsert_vuln({"cve": "CVE-TEST-1", "cvss": 5.0, "severity": "medium", "priority": 5.0}, reason="t")
    db.upsert_vuln({"cve": "CVE-TEST-1", "cvss": 9.8, "severity": "critical", "priority": 9.8}, reason="t")
    d = c.get("/v1/intel/vulns/CVE-TEST-1", headers=H).json()
    assert len(d["history"]) == 2  # new + revision, never overwritten
    q = c.get("/v1/intel/review", headers=H).json()
    assert any(i["cve"] == "CVE-TEST-1" for i in q)
    rid = next(i["id"] for i in q if i["cve"] == "CVE-TEST-1")
    assert c.post(f"/v1/intel/review/{rid}", json={"decision": "approved"}, headers=H).json()["status"] == "approved"
    assert c.post("/v1/intel/review/999999", json={"decision": "approved"}, headers=H).status_code == 404

def test_kev_parser_offline():
    raw = b"cveID,vendorProject,product,vulnerabilityName,dateAdded\nCVE-2024-0001,Acme,Widget,Bad Thing,2024-01-01\n"
    r = syncmod.sync_kev(raw=raw)
    assert r["records"] == 1
    d = c.get("/v1/intel/vulns/CVE-2024-0001", headers=H).json()
    assert d["kev"] == 1

def test_epss_parser_offline():
    raw = b"cve,epss,percentile\nCVE-2024-0002,0.42,0.9\n"
    r = syncmod.sync_epss(raw=raw)
    assert r["records"] == 1
    d = c.get("/v1/intel/vulns/CVE-2024-0002", headers=H).json()
    assert abs(d["epss"] - 0.42) < 1e-9

def test_nvd_parser_offline():
    raw = b'{"vulnerabilities": [{"cve": {"id": "CVE-2024-0003", "published": "2024-01-01", "lastModified": "2024-01-02", "descriptions": [{"lang": "en", "value": "desc"}], "metrics": {"cvssMetricV31": [{"cvssData": {"baseScore": 8.1, "baseSeverity": "HIGH"}}]}}}]}'
    r = syncmod.sync_nvd(raw=raw)
    assert r["records"] == 1
    d = c.get("/v1/intel/vulns/CVE-2024-0003", headers=H).json()
    assert d["cvss"] == 8.1 and d["severity"] == "high"

def test_auth_and_ordering():
    assert c.get("/v1/intel/vulns").status_code == 401
    top = c.get("/v1/intel/vulns?limit=5", headers=H).json()
    pris = [v["priority"] for v in top]
    assert pris == sorted(pris, reverse=True)
