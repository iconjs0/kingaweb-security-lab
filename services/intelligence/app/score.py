"""Effective priority: CVSS base + KEV bump + EPSS scaling + lab relevance.
Never auto-deploys anything — it only orders the human review queue."""
import json
import os

KEV_BUMP = 3.0
EPSS_WEIGHT = 2.0
LAB_BUMP = 1.0

def lab_map() -> dict:
    for cand in (os.environ.get("LAB_CVE_MAP", ""),
                 os.path.join(os.path.dirname(__file__), "..", "data", "lab-cve-map.json")):
        if cand and os.path.exists(cand):
            try:
                with open(cand) as f:
                    return json.load(f).get("cve_lab_relevance", {})
            except Exception:
                pass
    return {}

def severity_of(cvss: float) -> str:
    if cvss >= 9.0:
        return "critical"
    if cvss >= 7.0:
        return "high"
    if cvss >= 4.0:
        return "medium"
    if cvss > 0:
        return "low"
    return "none"

def priority(cvss: float, kev: bool, epss: float, labs: list) -> float:
    p = max(0.0, min(10.0, float(cvss or 0)))
    if kev:
        p += KEV_BUMP
    p += max(0.0, min(1.0, float(epss or 0))) * EPSS_WEIGHT
    if labs:
        p += LAB_BUMP
    return round(p, 2)
