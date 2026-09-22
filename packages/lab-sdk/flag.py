"""Shared per-session flag SDK — mirrored by services/api/app/flags.py (parity tested).
flag = KW{hex(HMAC_SHA256(key='kw-v1:'+seed, msg=session:objective))[:16]}
Seed lives only in API DB + target env (never in images, never logged)."""
import hashlib
import hmac

PREFIX = "KW{"

def mint(session_id: str, seed_hex: str, objective_id: str) -> str:
    key = ("kw-v1:" + seed_hex).encode()
    msg = f"{session_id}:{objective_id}".encode()
    return PREFIX + hmac.new(key, msg, hashlib.sha256).hexdigest()[:16] + "}"

def verify(candidate: str, session_id: str, seed_hex: str, objective_id: str) -> bool:
    try:
        return hmac.compare_digest(candidate.strip(), mint(session_id, seed_hex, objective_id))
    except Exception:
        return False
