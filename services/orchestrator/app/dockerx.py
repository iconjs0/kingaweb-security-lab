"""Thin Docker wrapper. Every container: own internal network, non-root,
read-only fs, CPU/mem/pid limits, loopback-published ports only."""
import time
import urllib.request

import docker
from docker.errors import NotFound

from .policy import LABEL

RUN_USER = "65532:65532"

_MEM = {"b": 1, "k": 1000, "m": 1000**2, "g": 1000**3,
        "ki": 1024, "mi": 1024**2, "gi": 1024**3}

def parse_mem(s: str) -> int:
    import re as _re
    m = _re.match(r"^\s*(\d+(?:\.\d+)?)\s*([KkMmGgBb]i?|[bB])?\s*$", str(s))
    if not m:
        raise ValueError(f"bad memory value: {s}")
    num, unit = float(m.group(1)), (m.group(2) or "b").lower()
    return int(num * _MEM[unit])

def client():
    return docker.from_env()

def create_network(cli, sid: str):
    return cli.networks.create(f"kw-{sid}", internal=True, labels={LABEL: sid})

def run_target(cli, sid: str, net, target: dict, resources: dict | None = None,
               env: dict[str, str] | None = None):
    # NOTE: no published ports — session nets are internal (Docker gives null
    # bindings there). Access flows via loopback relays (relay.py) instead.
    res = resources or {}
    container = cli.containers.run(
        target["runtime_image"],
        name=f"kw-{sid}-{target['name']}",
        detach=True,
        network=net.name,
        labels={LABEL: sid, "kingaweb.target": target["name"]},
        user=RUN_USER,
        read_only=True,
        tmpfs={"/tmp": "size=64m,mode=1777"},
        mem_limit=parse_mem(res.get("memory", "256m")),
        nano_cpus=int(float(res.get("cpu", "0.5")) * 1e9),
        pids_limit=res.get("pids", 64),
        cap_drop=["ALL"],
        security_opt=["no-new-privileges"],
        environment=env or {},
    )
    return container

def container_ip(container, net_name: str) -> str | None:
    container.reload()
    nets = container.attrs["NetworkSettings"]["Networks"] or {}
    return (nets.get(net_name) or {}).get("IPAddress") or None

def wait_ready(url: str, timeout_s: int = 30) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if r.status < 500:
                    return True
        except Exception:
            time.sleep(1)
    return False

def destroy_session(cli, sid: str) -> dict:
    removed = {"containers": 0, "networks": 0}
    for c in cli.containers.list(all=True, filters={"label": f"{LABEL}={sid}"}):
        try:
            c.remove(force=True)
            removed["containers"] += 1
        except Exception:
            pass
    for n in cli.networks.list(filters={"label": f"{LABEL}={sid}"}):
        try:
            n.remove()
            removed["networks"] += 1
        except Exception:
            pass
    return removed

def reconcile(cli, live: set[str]) -> dict:
    """Destroy labelled leftovers with no live lease (post-crash cleanup)."""
    out = {"containers": 0, "networks": 0}
    try:
        for c in cli.containers.list(all=True, filters={"label": LABEL}):
            sid = (c.labels or {}).get(LABEL, "")
            if sid and sid not in live:
                try:
                    c.remove(force=True)
                    out["containers"] += 1
                except Exception:
                    pass
        for n in cli.networks.list(filters={"label": LABEL}):
            sids = [v for k, v in (n.attrs.get("Labels") or {}).items() if k == LABEL]
            if sids and all(s not in live for s in sids):
                try:
                    n.remove()
                    out["networks"] += 1
                except Exception:
                    pass
    except Exception:
        pass
    return out

def exec_probe(container, cmd: str) -> tuple[int, str]:
    try:
        rc, out = container.exec_run(cmd, user=RUN_USER)
        return rc, out.decode("utf-8", "replace") if isinstance(out, bytes) else str(out)
    except Exception as e:
        return 999, f"exec error: {e}"

def get_notfound():
    return NotFound
