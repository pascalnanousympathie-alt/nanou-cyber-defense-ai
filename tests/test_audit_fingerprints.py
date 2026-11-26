import hashlib
import hmac
from types import SimpleNamespace

from pydantic import SecretStr

from nanou_cyber_ai import api
from nanou_cyber_ai.settings import settings


def test_audit_and_rate_limit_fingerprints_use_configured_hmac(monkeypatch) -> None:
    key = "unit-test-audit-hmac-key-32-bytes!"
    monkeypatch.setattr(settings, "audit_hmac_key", SecretStr(key))
    request = SimpleNamespace(client=SimpleNamespace(host="203.0.113.10"))

    expected_ip = hmac.new(key.encode(), b"203.0.113.10", hashlib.sha256).hexdigest()
    assert api._ip_digest(request) == expected_ip

    email, ip = api._rate_fingerprints(request, "analyst@example.test", "auth.login")
    expected_email = hmac.new(
        key.encode(), b"auth.login:analyst@example.test", hashlib.sha256
    ).hexdigest()
    expected_rate_ip = hmac.new(
        key.encode(), f"auth.login:{expected_ip}".encode(), hashlib.sha256
    ).hexdigest()

    assert email == expected_email
    assert ip == expected_rate_ip
    assert email != hashlib.sha256(b"auth.login:analyst@example.test").hexdigest()


def test_serverless_fingerprints_fail_closed_without_hmac_key(monkeypatch) -> None:
    monkeypatch.setattr(settings, "audit_hmac_key", None)
    monkeypatch.setenv("VERCEL", "1")
    request = SimpleNamespace(client=SimpleNamespace(host="203.0.113.10"))

    try:
        api._ip_digest(request)
    except RuntimeError as exc:
        assert "NANOU_AUDIT_HMAC_KEY" in str(exc)
    else:
        raise AssertionError("Hosted fingerprinting must require the HMAC key.")
