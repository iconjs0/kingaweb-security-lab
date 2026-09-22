"""Minimal Phase-0 manifest validator: python3 packages/lab-sdk/validate.py labs/"""
import sys, pathlib
try:
    import yaml
except ImportError:
    print("pyyaml not installed, skipping strict check (pip install pyyaml for full validation)")
    sys.exit(0)

required_top = ["apiVersion", "kind", "metadata", "targets", "objectives"]
errors = []
labs_root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "labs")
found = list(labs_root.rglob("lab.yaml"))
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
        if "@sha256:" not in img:
            errors.append(f"{f}: target {t.get('name')} image must be digest-pinned (@sha256:)")
        if t.get("privileged"):
            errors.append(f"{f}: privileged forbidden")
if errors:
    print("\n".join(errors)); sys.exit(1)
print(f"manifests OK ({len(found)} labs)")
