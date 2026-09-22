"""Image + manifest policy. Deny by default; allowlist + digest pinning.
Production: manifest image must be <repo>@sha256:<64hex> and repo allowlisted,
manifest must carry a signature block. Dev flags relax each (logged)."""
import json
import os
import pathlib
import re

import yaml

LABEL = "kingaweb.session"
SHA_RE = re.compile(r"^(.+)@sha256:([0-9a-f]{64})$")

class PolicyError(Exception):
    pass

def labs_root() -> pathlib.Path:
    env = os.environ.get("LABS_ROOT", "")
    if env and pathlib.Path(env).exists():
        return pathlib.Path(env)
    cur = pathlib.Path(__file__).resolve().parent.parent.parent.parent
    for _ in range(6):
        if (cur / "labs" / "kingaweb-native").exists():
            return cur / "labs"
        cur = cur.parent
    return pathlib.Path.cwd() / "labs"

def image_map() -> dict[str, str]:
    raw = os.environ.get("ORCH_IMAGE_MAP", '{"local/kingaweb-mpesa-mock": "local-mpesa-mock"}')
    try:
        return json.loads(raw)
    except Exception:
        return {}

def allowlist() -> set[str]:
    return {s.strip() for s in os.environ.get("ORCH_ALLOWLIST", "local-mpesa-mock").split(",") if s.strip()}

def load_manifest(slug: str, version: str) -> dict:
    for f in labs_root().rglob("lab.yaml"):
        try:
            d = yaml.safe_load(f.read_text())
        except Exception:
            continue
        md = (d or {}).get("metadata", {})
        if md.get("slug") == slug and str(md.get("version")) == str(version):
            return d
    raise PolicyError(f"manifest not found: {slug}@{version}")

def check_manifest(d: dict) -> None:
    for k in ("apiVersion", "kind", "metadata", "targets", "objectives"):
        if k not in d:
            raise PolicyError(f"manifest missing {k}")
    if d.get("kind") != "Lab":
        raise PolicyError("manifest kind must be Lab")
    for t in d.get("targets", []):
        for banned in ("privileged", "hostNetwork", "mountDockerSock", "hostPid", "hostIpc"):
            if t.get(banned):
                raise PolicyError(f"target {t.get('name')}: {banned} forbidden")
    if not d.get("signature"):
        if os.environ.get("ALLOW_UNSIGNED_MANIFESTS", "false").lower() != "true":
            raise PolicyError("manifest signature required (or ALLOW_UNSIGNED_MANIFESTS=true in dev)")
    ttl = int(d.get("session", {}).get("ttlMinutes", 60))
    if ttl > 60 or ttl < 1:
        raise PolicyError("session.ttlMinutes must be 1..60")

def resolve_image(manifest_image: str) -> tuple[str, str | None, bool]:
    """Return (runtime_image, pinned_digest_or_None, is_dev_placeholder)."""
    m = SHA_RE.match(manifest_image)
    if m:
        repo, digest = m.group(1), m.group(2)
        runtime = image_map().get(repo, repo)
        if runtime not in allowlist():
            raise PolicyError(f"image repo not allowlisted: {runtime}")
        return runtime, digest, False
    # dev placeholder form: local/<repo>@sha256:LOCAL_BUILD (or bare local/<repo>)
    repo = manifest_image.split("@")[0]
    runtime = image_map().get(repo, None)
    if repo.startswith("local/") and runtime and runtime in allowlist():
        if os.environ.get("ALLOW_DEV_DIGESTS", "false").lower() != "true":
            raise PolicyError("dev digest placeholder requires ALLOW_DEV_DIGESTS=true")
        return runtime, None, True
    raise PolicyError(f"image must be digest-pinned and allowlisted: {manifest_image}")
