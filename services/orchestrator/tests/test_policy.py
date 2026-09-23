"""Policy unit tests (no docker)."""
import os
os.environ.setdefault("ALLOW_UNSIGNED_MANIFESTS", "true")
os.environ.setdefault("ALLOW_DEV_DIGESTS", "true")
os.environ.setdefault("ORCH_ALLOWLIST", "local-mpesa-mock")
os.environ.setdefault("ORCH_IMAGE_MAP", '{"local/kingaweb-mpesa-mock": "local-mpesa-mock"}')

import pathlib
import pytest
from app import policy

REPO = pathlib.Path(__file__).resolve().parent.parent.parent.parent

def test_load_and_check_mpesa():
    d = policy.load_manifest("mpesa-bola-01", "0.1.0")
    policy.check_manifest(d)

def test_banned_fields_rejected():
    d = policy.load_manifest("mpesa-bola-01", "0.1.0")
    d["targets"][0]["privileged"] = True
    with pytest.raises(policy.PolicyError):
        policy.check_manifest(d)

def test_resolve_dev_placeholder():
    runtime, pinned, dev = policy.resolve_image("local/kingaweb-mpesa-mock@sha256:LOCAL_BUILD")
    assert runtime == "local-mpesa-mock" and dev is True

def test_unpinned_rejected():
    with pytest.raises(policy.PolicyError):
        policy.resolve_image("ghcr.io/evil/lab:latest")

def test_unknown_manifest():
    with pytest.raises(policy.PolicyError):
        policy.load_manifest("nope", "9.9.9")

def test_writable_needs_curated_exception():
    d = policy.load_manifest("mpesa-bola-01", "0.1.0")
    d["targets"][0]["writableFs"] = True
    with pytest.raises(policy.PolicyError):
        policy.check_manifest(d)
    d["origin"] = {"thirdParty": True}
    d["targets"][0]["exception"] = "reviewed: needs writes"
    policy.check_manifest(d)  # passes with origin + justification

def test_curated_wrapper_loads():
    d = policy.load_manifest("curated-juice-shop", "0.1.0")
    policy.check_manifest(d)
    os.environ["ORCH_ALLOWLIST"] = "local-mpesa-mock,bkimminich/juice-shop"
    try:
        runtime, pinned, dev = policy.resolve_image(
            "bkimminich/juice-shop@sha256:73c53fbf442e8337b3ea3d98c7e8550308854701ebdfce4cc39768f36b75430e")
        assert pinned and dev is False
    finally:
        os.environ["ORCH_ALLOWLIST"] = "local-mpesa-mock"
