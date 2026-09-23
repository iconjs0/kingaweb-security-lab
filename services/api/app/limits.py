"""Edge guards: token-bucket rate limits, security headers, in-memory metrics.
Quotas (per-user/global active sessions) live in routers.launch (needs DB)."""
import os
import time
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

_buckets: dict[str, list[float]] = defaultdict(list)
metrics: dict[str, int] = defaultdict(int)

def _cfg(name: str, default: int) -> int:
    try:
        return max(1, int(os.environ.get(name, default)))
    except ValueError:
        return default

LIMITS = [
    ("POST", "/v1/auth/login", "RATE_LIMIT_LOGIN_PER_MIN", 60),
    ("POST", "/v1/sessions", "RATE_LIMIT_LAUNCH_PER_MIN", 30),
    ("POST", "/submissions", "RATE_LIMIT_SUBMIT_PER_MIN", 120),
]

def _key(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    who = auth[-12:] if auth else (request.client.host if request.client else "unknown")
    return f"{request.method}:{request.url.path}:{who}"

def _allow(key: str, per_min: int) -> bool:
    now = time.time()
    hist = [t for t in _buckets[key] if now - t < 60]
    _buckets[key] = hist
    if len(hist) >= per_min:
        return False
    hist.append(now)
    return True

def _secure(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "same-origin"
    resp.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    resp.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
    if os.environ.get("ENABLE_HSTS", "false").lower() == "true":
        resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return resp

class GuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        metrics["requests"] += 1
        for method, prefix, env, default in LIMITS:
            if request.method == method and prefix in request.url.path:
                if not _allow(_key(request), _cfg(env, default)):
                    metrics["rate_limited"] += 1
                    return _secure(JSONResponse({"detail": "rate limited, slow down"}, status_code=429))
                break
        return _secure(await call_next(request))
