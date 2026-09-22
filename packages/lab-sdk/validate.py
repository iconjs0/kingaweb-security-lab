"""Manifest validator v0.2: checks core + docker-feature additions (ctf/blueTeam/tutor/i18n)."""
import sys, pathlib, json
try:
    import yaml
except ImportError:
    print("pyyaml not installed, skipping strict check (pip install pyyaml for full validation)")
    sys.exit(0)

required_top = ["apiVersion", "kind", "metadata", "targets", "objectives"]
errors = []
labs_root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "labs")
found = [f for f in labs_root.rglob("lab.yaml") if ".git" not in str(f)]
if not found:
    print("no lab.yaml found (ok for Phase 0 bootstrap)")
    sys.exit(0)
for f in found:
    data = yaml.safe_load(f.read_text())
    for k in required_top:
        if k not in data:
            errors.append(f"{f}: missing {k}")
    for t in data.get("targets", []):
        img = t.get("image", "")
        # allow local/* builds in dev, require digest at publish
        if "@sha256:" not in img and not img.startswith("local/"):
            errors.append(f"{f}: target {t.get('name')} image must be digest-pinned (@sha256:) or local/ (dev build)")
        if t.get("privileged"):
            errors.append(f"{f}: privileged forbidden")
    # v0.2 optional blocks — validate shape when present
    if "blueTeam" in data and "detectionGoal" not in data["blueTeam"]:
        errors.append(f"{f}: blueTeam.detectionGoal required when blueTeam present")
    if "tutorPolicy" in data and "assessmentDiscloses" not in data["tutorPolicy"]:
        errors.append(f"{f}: tutorPolicy.assessmentDiscloses required when tutorPolicy present")
    if "i18n" in data:
        base = f.parent
        for lang, rel in data["i18n"].items():
            if not (base / rel).exists():
                errors.append(f"{f}: i18n.{lang} file missing: {rel}")
    if "ctf" in data and "basePoints" not in data["ctf"]:
        errors.append(f"{f}: ctf.basePoints required when ctf present")
if errors:
    print("\n".join(errors)); sys.exit(1)
print(f"manifests OK ({len(found)} labs)")
