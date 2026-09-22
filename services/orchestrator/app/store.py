"""Leases + lifecycle events (no exploit payloads stored)."""
import threading
import time

_lock = threading.Lock()
_leases: dict[str, dict] = {}   # sid -> {expires_at, lab, targets}
_events: list[dict] = []
_relays: dict[str, list] = {}   # sid -> relay servers (closed on destroy/expire)

def upsert(sid: str, lab: str, ttl_minutes: int, targets: list[dict]) -> float:
    exp = time.time() + ttl_minutes * 60
    with _lock:
        _leases[sid] = {"expires_at": exp, "lab": lab, "targets": targets}
        _events.append({"sid": sid, "event": "provision", "lab": lab, "at": time.time()})
    return exp

def touch(sid: str, minutes: int) -> float | None:
    with _lock:
        if sid not in _leases:
            return None
        _leases[sid]["expires_at"] += minutes * 60
        _events.append({"sid": sid, "event": "extend", "at": time.time()})
        return _leases[sid]["expires_at"]

def drop(sid: str, why: str) -> None:
    with _lock:
        _leases.pop(sid, None)
        servers = _relays.pop(sid, [])
        _events.append({"sid": sid, "event": why, "at": time.time()})
    for srv in servers:
        try:
            from . import relay as _relay
            _relay.stop(srv)
        except Exception:
            pass

def add_relays(sid: str, servers: list) -> None:
    with _lock:
        _relays.setdefault(sid, []).extend(servers)

def expired() -> list[str]:
    now = time.time()
    with _lock:
        return [s for s, l in _leases.items() if l["expires_at"] <= now]

def live() -> set[str]:
    with _lock:
        return set(_leases)

def events(n: int = 100) -> list[dict]:
    with _lock:
        return list(_events[-n:])
