"""SQLite store: vulns + immutable severity history + review queue. stdlib only."""
import os
import sqlite3
import time

def path() -> str:
    return os.environ.get("INTEL_DB", "/tmp/opencode-intel.db")

def conn() -> sqlite3.Connection:
    c = sqlite3.connect(path())
    c.row_factory = sqlite3.Row
    return c

SCHEMA = """
CREATE TABLE IF NOT EXISTS vulns(
  cve TEXT PRIMARY KEY, published TEXT, modified TEXT,
  cvss REAL DEFAULT 0, severity TEXT DEFAULT 'none', description TEXT DEFAULT '',
  kev INTEGER DEFAULT 0, epss REAL DEFAULT 0, priority REAL DEFAULT 0,
  labs TEXT DEFAULT '[]', updated_at REAL DEFAULT 0);
CREATE TABLE IF NOT EXISTS severity_history(
  id INTEGER PRIMARY KEY AUTOINCREMENT, cve TEXT, cvss REAL, severity TEXT,
  reason TEXT DEFAULT '', at REAL);
CREATE TABLE IF NOT EXISTS review_queue(
  id INTEGER PRIMARY KEY AUTOINCREMENT, cve TEXT, reason TEXT,
  status TEXT DEFAULT 'open', created_at REAL);
CREATE TABLE IF NOT EXISTS sync_runs(
  id INTEGER PRIMARY KEY AUTOINCREMENT, feed TEXT, started REAL,
  finished REAL, records INTEGER DEFAULT 0, error TEXT DEFAULT '');
"""

def init() -> None:
    os.makedirs(os.path.dirname(path()) or ".", exist_ok=True)
    c = conn()
    try:
        c.executescript(SCHEMA)
        c.commit()
    finally:
        c.close()

def upsert_vuln(v: dict, reason: str = "") -> str:
    """Insert/update vuln; append history on new CVE or severity change; queue review."""
    c = conn()
    try:
        old = c.execute("SELECT cvss, severity, kev FROM vulns WHERE cve=?", (v["cve"],)).fetchone()
        now = time.time()
        c.execute(
            "INSERT INTO vulns(cve,published,modified,cvss,severity,description,kev,epss,priority,labs,updated_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?)"
            " ON CONFLICT(cve) DO UPDATE SET published=excluded.published, modified=excluded.modified,"
            " cvss=excluded.cvss, severity=excluded.severity, description=excluded.description,"
            " kev=max(vulns.kev,excluded.kev), epss=excluded.epss, priority=excluded.priority,"
            " labs=excluded.labs, updated_at=excluded.updated_at",
            (v["cve"], v.get("published", ""), v.get("modified", ""), v.get("cvss", 0),
             v.get("severity", "none"), v.get("description", "")[:2000], 1 if v.get("kev") else 0,
             v.get("epss", 0), v.get("priority", 0), v.get("labs", "[]"), now))
        event = None
        if not old:
            event = "new"
        elif (old["severity"], old["cvss"]) != (v.get("severity", "none"), v.get("cvss", 0)):
            event = f"severity {old['severity']}/{old['cvss']} -> {v.get('severity')}/{v.get('cvss')}"
        elif v.get("kev") and not old["kev"]:
            event = "added to KEV"
        if event:
            c.execute("INSERT INTO severity_history(cve,cvss,severity,reason,at) VALUES(?,?,?,?,?)",
                      (v["cve"], v.get("cvss", 0), v.get("severity", "none"), f"{event} {reason}".strip(), now))
            open_row = c.execute("SELECT id FROM review_queue WHERE cve=? AND status='open'",
                                 (v["cve"],)).fetchone()
            if not open_row:
                c.execute("INSERT INTO review_queue(cve,reason,status,created_at) VALUES(?,?,?,?)",
                          (v["cve"], event, "open", now))
        c.commit()
        return event or "unchanged"
    finally:
        c.close()
