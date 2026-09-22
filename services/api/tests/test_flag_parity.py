"""Flag parity: API implementation must agree with the shared target SDK."""
import importlib.util
import os

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
os.environ.setdefault("FLAG_HMAC_SECRET", "test-secret-32-bytes-minimum-ok")

from app import flags as api_flags  # noqa: E402

spec = importlib.util.spec_from_file_location("labflag", os.path.join(REPO, "packages", "lab-sdk", "flag.py"))
labflag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(labflag)

def test_parity():
    for sid, seed, obj in [("s-abc", "deadbeef" * 4, "o1"), ("s-x", "00" * 16, "read-other-order")]:
        assert api_flags.mint_flag(sid, "0.1.0", obj, seed) == labflag.mint(sid, seed, obj)
        assert labflag.verify(api_flags.mint_flag(sid, "9.9.9", obj, seed), sid, seed, obj)
        assert api_flags.verify_flag(labflag.mint(sid, seed, obj), sid, "0.1.0", obj, seed)
