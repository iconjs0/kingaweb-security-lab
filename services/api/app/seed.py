"""Seed labs table from labs/*/lab.yaml manifests (versioned, idempotent upsert)."""
import json
import pathlib
from sqlalchemy.orm import Session as DBSession
from .models import Lab

try:
    import yaml
except ImportError:
    yaml = None

def seed_labs(db: DBSession, labs_root: str = "labs") -> int:
    if yaml is None:
        return 0
    root = pathlib.Path(labs_root)
    if not root.exists():
        return 0
    n = 0
    for f in sorted(root.rglob("lab.yaml")):
        try:
            d = yaml.safe_load(f.read_text())
        except Exception:
            continue
        md = d.get("metadata", {})
        slug, version = md.get("slug"), md.get("version")
        if not slug or not version:
            continue
        tracks = d.get("tracks", ["web"])
        ow = d.get("owasp", {})
        row = db.query(Lab).filter(Lab.slug == slug, Lab.version == version).first()
        vals = dict(
            title=md.get("title", slug), summary=md.get("summary", ""),
            track=(tracks[0] if tracks else "web"), difficulty=md.get("difficulty", "beginner"),
            time_minutes=int(md.get("timeMinutes", 60)),
            ttl_minutes=min(60, int(d.get("session", {}).get("ttlMinutes", 60))),
            objectives_json=json.dumps([
                {"id": o.get("id"), "title": o.get("title", o.get("id")),
                 "owasp": ow, "cwe": d.get("cwe", [])}
                for o in d.get("objectives", [])]),
            targets_json=json.dumps([
                {"name": t.get("name"), "ports": t.get("ports", []),
                 "allow_host": t.get("name")}
                for t in d.get("targets", [])]),
        )
        if row:
            for k, v in vals.items():
                setattr(row, k, v)
        else:
            db.add(Lab(slug=slug, version=version, **vals))
        n += 1
    db.commit()
    return n
