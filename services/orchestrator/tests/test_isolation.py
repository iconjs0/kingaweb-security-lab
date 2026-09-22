"""Isolation tests (need local docker + built local-mpesa-mock image).
Run: .venv/bin/pytest tests/test_isolation.py -q (skips if docker/image absent)."""
import os
import time
import urllib.request

import pytest

docker = pytest.importorskip("docker")
from app import dockerx, policy  # noqa: E402

os.environ.setdefault("ALLOW_UNSIGNED_MANIFESTS", "true")
os.environ.setdefault("ALLOW_DEV_DIGESTS", "true")
os.environ.setdefault("ORCH_ALLOWLIST", "local-mpesa-mock")
os.environ.setdefault("ORCH_IMAGE_MAP", '{"local/kingaweb-mpesa-mock": "local-mpesa-mock"}')

try:
    _cli = docker.from_env()
    _cli.ping()
    _cli.images.get("local-mpesa-mock")
except Exception:
    pytest.skip("docker or local-mpesa-mock image unavailable", allow_module_level=True)

def _provision(sid):
    from app import relay as relay_mod
    cli = docker.from_env()
    dockerx.destroy_session(cli, sid)  # idempotent retry
    d = policy.load_manifest("mpesa-bola-01", "0.1.0")
    policy.check_manifest(d)
    tgts = []
    for t in d["targets"]:
        runtime, _, _ = policy.resolve_image(t["image"])
        tgts.append({"name": t["name"], "runtime_image": runtime, "ports": t["ports"],
                     "health": t.get("healthcheck", {}), "resources": t.get("resources", {})})
    net = dockerx.create_network(cli, sid)
    cons = [dockerx.run_target(cli, sid, net, t, t.get("resources")) for t in tgts]
    ip = None
    for _ in range(30):
        ip = dockerx.container_ip(cons[0], net.name)
        if ip:
            break
        time.sleep(1)
    assert ip and dockerx.wait_ready(f"http://{ip}:5009/healthz")
    srv, hp = relay_mod.start("127.0.0.1", ip, 5009)
    with urllib.request.urlopen(f"http://127.0.0.1:{hp}/rates", timeout=5) as r:
        assert r.status == 200
    return cli, cons, hp, srv, relay_mod

def _teardown(sid, srv, relay_mod):
    relay_mod.stop(srv)
    dockerx.destroy_session(docker.from_env(), sid)

def test_two_sessions_isolated():
    cli1, cons1, hp1, srv1, rm = _provision("iso-a")
    cli2, cons2, hp2, srv2, _ = _provision("iso-b")
    try:
        assert hp1 != hp2  # distinct loopback relays, no shared state
        with urllib.request.urlopen(f"http://127.0.0.1:{hp1}/rates", timeout=5) as r:
            assert r.status == 200
        # cross-session: container A cannot resolve/reach session B network
        rc, _ = dockerx.exec_probe(cons1[0], "python -c 'import socket;socket.gethostbyname(\"kw-iso-b-mpesa-mock\")'")
        assert rc != 0
    finally:
        _teardown("iso-a", srv1, rm)
        _teardown("iso-b", srv2, rm)

def test_no_egress_and_no_metadata():
    cli, cons, hp, srv, rm = _provision("iso-c")
    try:
        rc, _ = dockerx.exec_probe(cons[0], "python -c 'import socket;socket.create_connection((\"8.8.8.8\",53),timeout=3)'")
        assert rc != 0  # internal network: no internet egress
        rc, _ = dockerx.exec_probe(cons[0], "python -c 'import urllib.request;urllib.request.urlopen(\"http://169.254.169.254/\",timeout=3)'")
        assert rc != 0  # no host metadata
    finally:
        _teardown("iso-c", srv, rm)

def test_hardening_attrs_and_cleanup():
    cli, cons, hp, srv, rm = _provision("iso-d")
    c = cons[0]
    c.reload()
    assert c.attrs["HostConfig"]["ReadonlyRootfs"] is True
    assert c.attrs["HostConfig"]["PidsLimit"] == 32
    assert c.attrs["Config"]["User"] == "65532:65532"
    _teardown("iso-d", srv, rm)
    leftovers = cli.containers.list(all=True, filters={"label": "kingaweb.session=iso-d"})
    assert leftovers == []
