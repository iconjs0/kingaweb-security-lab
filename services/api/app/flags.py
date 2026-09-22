"""Per-session seed-bound flags — mirrors packages/lab-sdk/flag.py (parity tested).
flag = KW{hex(HMAC_SHA256(key='kw-v1:'+seed, msg=session:objective))[:16]}
Targets mint via SESSION_SEED/SESSION_ID env (injected by orchestrator, never
baked into images); API verifies from the stored seed. Only hashes stored."""
import hashlib
import hmac
import os
import secrets

PREFIX = "KW{"

def hmac_secret() -> str:
    # retained for session provisioning entropy checks; flags are seed-bound (see above)
    s = os.environ.get("FLAG_HMAC_SECRET", "")
    if len(s) < 16:
        raise RuntimeError("FLAG_HMAC_SECRET missing or too short (>=16 chars)")
    return s

def new_seed_hex(nbytes: int = 16) -> str:
    return secrets.token_hex(nbytes)

def mint_flag(session_id: str, lab_version: str, objective_id: str, seed_hex: str) -> str:
    key = ("kw-v1:" + seed_hex).encode()
    msg = f"{session_id}:{objective_id}".encode()
    return PREFIX + hmac.new(key, msg, hashlib.sha256).hexdigest()[:16] + "}"

def verify_flag(candidate: str, session_id: str, lab_version: str, objective_id: str, seed_hex: str) -> bool:
    try:
        return hmac.compare_digest(candidate.strip(), mint_flag(session_id, lab_version, objective_id, seed_hex))
    except Exception:
        return False

def flag_hash(candidate: str) -> str:
    return hashlib.sha256(candidate.strip().encode()).hexdigest()

def score_solve(base: int, solves_before: int, hint_cost: int = 0, attempts: int = 1,
                first_blood: bool = False, remediation: bool = False, floor: int = 100) -> int:
    pts = max(floor, int(base * (0.9 ** max(0, solves_before))))
    if first_blood:
        pts = int(pts * 1.1)
    pts -= max(0, hint_cost) + max(0, attempts - 1) * 2
    if remediation:
        pts += 25
    return max(floor // 2, pts)
