from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from pydantic import SecretStr

from nanou_cyber_ai.api import app
from nanou_cyber_ai.settings import settings
from nanou_cyber_ai.storage.auth import AuthStore
from nanou_cyber_ai.storage.database import SecurityDatabase


def _admin(store: AuthStore):
    return store.create_bootstrap_admin(
        email="admin@example.test",
        display_name="First Admin",
        password_hash="test-only-argon2id-hash",
        request_id="test-bootstrap",
        ip_digest="b" * 64,
    )


def test_bootstrap_is_one_time_and_registers_pending_viewers(tmp_path) -> None:
    database = SecurityDatabase(None, tmp_path)
    store = AuthStore(database)

    assert store.bootstrap_available() is True
    admin = _admin(store)
    assert admin is not None
    assert admin["role"] == "admin"
    assert admin["is_active"] is True
    assert store.bootstrap_available() is False
    assert _admin(store) is None

    viewer = store.register(
        email="viewer@example.test",
        display_name="Pending Viewer",
        password_hash="another-test-hash",
        request_id="test-registration",
        ip_digest="c" * 64,
    )
    assert viewer["role"] == "viewer"
    assert viewer["is_approved"] is False
    assert viewer["is_active"] is False

    events = store.list_audit_events()
    assert {event["action"] for event in events} >= {"auth.bootstrap", "auth.register"}
    database.close()


def test_role_change_approves_and_revokes_existing_sessions(tmp_path) -> None:
    database = SecurityDatabase(None, tmp_path)
    store = AuthStore(database)
    admin = _admin(store)
    viewer = store.register(
        email="analyst@example.test",
        display_name="Pending Analyst",
        password_hash="test-hash",
        request_id=None,
        ip_digest=None,
    )
    token = "session-token-for-test"
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    store.create_session(
        user_id=viewer["id"],
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + timedelta(hours=2),
    )

    approved = store.update_user(
        actor_user_id=admin["id"],
        target_user_id=viewer["id"],
        role="analyst",
        is_active=True,
        request_id="test-approval",
        ip_digest=None,
    )
    assert approved["role"] == "analyst"
    assert approved["is_approved"] is True
    assert approved["is_active"] is True
    assert store.get_user_for_session(token_hash) is None
    database.close()


def test_last_active_admin_cannot_be_demoted_or_deactivated(tmp_path) -> None:
    database = SecurityDatabase(None, tmp_path)
    store = AuthStore(database)
    admin = _admin(store)

    try:
        store.update_user(
            actor_user_id=admin["id"],
            target_user_id=admin["id"],
            role="viewer",
            is_active=False,
            request_id=None,
            ip_digest=None,
        )
    except ValueError as exc:
        assert "cannot demote" in str(exc)
    else:
        raise AssertionError("Self-demotion should be rejected.")

    database.close()


def _csrf(client: TestClient) -> str:
    response = client.get("/api/auth/csrf")
    assert response.status_code == 200
    return response.json()["csrf_token"]


def test_web_auth_bootstrap_register_approve_and_rbac(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "database_url", None)
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "auth_attempts_per_window", 50)
    monkeypatch.setattr(
        settings,
        "bootstrap_token",
        SecretStr("test-bootstrap-token-long-enough-1234567890"),
    )

    with TestClient(app) as admin_client:
        csrf = _csrf(admin_client)
        bootstrap = admin_client.post(
            "/api/auth/bootstrap",
            headers={"X-CSRF-Token": csrf},
            json={
                "email": "admin@example.test",
                "display_name": "First Admin",
                "password": "Correct-Horse-Battery-42!",
                "bootstrap_token": "test-bootstrap-token-long-enough-1234567890",
            },
        )
        assert bootstrap.status_code == 200
        assert bootstrap.json()["user"]["role"] == "admin"
        assert settings.session_cookie_name in admin_client.cookies

        current = admin_client.get("/api/auth/me")
        assert current.status_code == 200
        assert current.json()["authenticated"] is True
        assert current.json()["user"]["role"] == "admin"

        repeated = admin_client.post(
            "/api/auth/bootstrap",
            headers={"X-CSRF-Token": csrf},
            json={
                "email": "second@example.test",
                "display_name": "Second Admin",
                "password": "Different-Password-44!",
                "bootstrap_token": "test-bootstrap-token-long-enough-1234567890",
            },
        )
        assert repeated.status_code == 409

        registration = admin_client.post(
            "/api/auth/register",
            headers={"X-CSRF-Token": csrf},
            json={
                "email": "analyst@example.test",
                "display_name": "Pending Analyst",
                "password": "Another-Strong-Password-51!",
            },
        )
        assert registration.status_code == 202
        pending_user_id = registration.json()["user"]["id"]

        with TestClient(app) as pending_client:
            pending_csrf = _csrf(pending_client)
            pending_login = pending_client.post(
                "/api/auth/login",
                headers={"X-CSRF-Token": pending_csrf},
                json={
                    "email": "analyst@example.test",
                    "password": "Another-Strong-Password-51!",
                },
            )
            assert pending_login.status_code == 403

        approval = admin_client.patch(
            f"/api/admin/users/{pending_user_id}",
            headers={"X-CSRF-Token": csrf},
            json={"role": "analyst", "is_active": True},
        )
        assert approval.status_code == 200
        assert approval.json()["is_approved"] is True

    with TestClient(app) as analyst_client:
        analyst_csrf = _csrf(analyst_client)
        login = analyst_client.post(
            "/api/auth/login",
            headers={"X-CSRF-Token": analyst_csrf},
            json={
                "email": "analyst@example.test",
                "password": "Another-Strong-Password-51!",
            },
        )
        assert login.status_code == 200
        assert login.json()["user"]["role"] == "analyst"

        denied = analyst_client.get("/api/admin/users")
        assert denied.status_code == 403

        allowed_metadata = analyst_client.get("/api/malware/metadata")
        assert allowed_metadata.status_code == 200


def test_bootstrap_requires_secret_and_does_not_claim_first_admin(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "database_url", None)
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "bootstrap_token", None)

    with TestClient(app) as client:
        csrf = _csrf(client)
        denied = client.post(
            "/api/auth/bootstrap",
            headers={"X-CSRF-Token": csrf},
            json={
                "email": "attacker@example.test",
                "display_name": "Attacker",
                "password": "Strong-Password-999!",
                "bootstrap_token": "attacker-controlled-token-is-not-valid-123456",
            },
        )
        assert denied.status_code == 403
        assert client.get("/api/auth/me").json()["bootstrap_required"] is True


def test_csrf_and_unauthenticated_access_are_rejected(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "database_url", None)
    monkeypatch.setattr(settings, "data_dir", tmp_path)

    with TestClient(app) as client:
        missing_csrf = client.post(
            "/api/auth/register",
            json={
                "email": "user@example.test",
                "display_name": "Test User",
                "password": "A-Strong-Password-55!",
            },
        )
        assert missing_csrf.status_code == 403

        csrf = _csrf(client)
        denied = client.get("/api/malware/metadata")
        assert denied.status_code == 401
        assert csrf


def test_viewer_role_is_read_only_and_admin_audit_is_restricted(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "database_url", None)
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "auth_attempts_per_window", 50)
    monkeypatch.setattr(
        settings,
        "bootstrap_token",
        SecretStr("test-bootstrap-token-long-enough-1234567890"),
    )

    with TestClient(app) as admin_client:
        admin_csrf = _csrf(admin_client)
        bootstrap = admin_client.post(
            "/api/auth/bootstrap",
            headers={"X-CSRF-Token": admin_csrf},
            json={
                "email": "owner@example.test",
                "display_name": "Owner Admin",
                "password": "Owner-Strong-Password-42!",
                "bootstrap_token": "test-bootstrap-token-long-enough-1234567890",
            },
        )
        assert bootstrap.status_code == 200

        registration = admin_client.post(
            "/api/auth/register",
            headers={"X-CSRF-Token": admin_csrf},
            json={
                "email": "viewer@example.test",
                "display_name": "Read Only Viewer",
                "password": "Viewer-Strong-Password-55!",
            },
        )
        assert registration.status_code == 202
        viewer_id = registration.json()["user"]["id"]

        approval = admin_client.patch(
            f"/api/admin/users/{viewer_id}",
            headers={"X-CSRF-Token": admin_csrf},
            json={"role": "viewer", "is_active": True},
        )
        assert approval.status_code == 200
        assert approval.json()["is_approved"] is True
        assert approval.json()["is_active"] is True

        audit = admin_client.get("/api/admin/audit?limit=30")
        assert audit.status_code == 200
        assert {event["action"] for event in audit.json()} >= {
            "auth.bootstrap",
            "auth.register",
            "admin.user.update",
        }

    with TestClient(app) as viewer_client:
        viewer_csrf = _csrf(viewer_client)
        login = viewer_client.post(
            "/api/auth/login",
            headers={"X-CSRF-Token": viewer_csrf},
            json={
                "email": "viewer@example.test",
                "password": "Viewer-Strong-Password-55!",
            },
        )
        assert login.status_code == 200
        assert login.json()["user"]["role"] == "viewer"

        allowed_metadata = viewer_client.get("/api/malware/metadata")
        denied_users = viewer_client.get("/api/admin/users")
        denied_audit = viewer_client.get("/api/admin/audit")
        denied_metadata_write = viewer_client.post(
            "/api/malware/metadata",
            headers={"X-CSRF-Token": viewer_csrf},
            json={
                "sha256": "a" * 64,
                "label": "malicious",
                "source": "viewer regression test",
            },
        )
        denied_feature_prepare = viewer_client.post(
            "/api/malware/features/prepare/ember2024-apk",
            headers={"X-CSRF-Token": viewer_csrf},
            content="",
        )

        assert allowed_metadata.status_code == 200
        assert denied_users.status_code == 403
        assert denied_audit.status_code == 403
        assert denied_metadata_write.status_code == 403
        assert denied_feature_prepare.status_code == 403


def test_developer_api_keys_are_hashed_scoped_rate_limited_and_revocable(tmp_path) -> None:
    database = SecurityDatabase(None, tmp_path)
    store = AuthStore(database)
    admin = _admin(store)
    token = "ncd_live_test-only-random-token-value"
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    created = store.create_api_key(
        owner_user_id=admin["id"],
        name="AI security assistant",
        token_prefix=token[:20],
        token_hash=token_hash,
        scopes=["intel:read"],
        expires_at=datetime.now(UTC) + timedelta(days=30),
        request_id="test-api-key-create",
        ip_digest=None,
    )
    assert created["name"] == "AI security assistant"
    assert created["scopes"] == ["intel:read"]
    assert "token_hash" not in created
    assert "token" not in created

    listed = store.list_api_keys(admin["id"])
    assert len(listed) == 1
    assert listed[0]["token_prefix"] == token[:20]
    principal = store.get_api_key_principal(token_hash)
    assert principal is not None
    assert principal["api_key_scopes"] == ["intel:read"]
    assert principal["role"] == "admin"

    assert store.consume_api_key_request(created["id"], maximum=2) is True
    assert store.consume_api_key_request(created["id"], maximum=2) is True
    assert store.consume_api_key_request(created["id"], maximum=2) is False

    revoked = store.revoke_api_key(
        owner_user_id=admin["id"],
        key_id=created["id"],
        request_id="test-api-key-revoke",
        ip_digest=None,
    )
    assert revoked is not None
    assert revoked["revoked_at"] is not None
    assert store.get_api_key_principal(token_hash) is None
    assert {event["action"] for event in store.list_audit_events()} >= {
        "developer.api_key.create",
        "developer.api_key.revoke",
    }
    database.close()


def test_user_role_change_revokes_owned_developer_api_keys(tmp_path) -> None:
    database = SecurityDatabase(None, tmp_path)
    store = AuthStore(database)
    admin = _admin(store)
    analyst = store.register(
        email="api-analyst@example.test",
        display_name="API Analyst",
        password_hash="test-hash",
        request_id=None,
        ip_digest=None,
    )
    approved = store.update_user(
        actor_user_id=admin["id"],
        target_user_id=analyst["id"],
        role="analyst",
        is_active=True,
        request_id="test-api-analyst-approval",
        ip_digest=None,
    )
    token_hash = hashlib.sha256(b"ncd_live_analyst-token").hexdigest()
    store.create_api_key(
        owner_user_id=approved["id"],
        name="Temporary analyst key",
        token_prefix="ncd_live_analyst",
        token_hash=token_hash,
        scopes=["intel:read"],
        expires_at=datetime.now(UTC) + timedelta(days=7),
        request_id=None,
        ip_digest=None,
    )

    store.update_user(
        actor_user_id=admin["id"],
        target_user_id=analyst["id"],
        role="analyst",
        is_active=False,
        request_id="test-api-analyst-disable",
        ip_digest=None,
    )
    assert store.get_api_key_principal(token_hash) is None
    assert store.list_api_keys(analyst["id"])[0]["revoked_at"] is not None
    database.close()


def test_password_rotation_requires_current_password_and_revokes_prior_sessions(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.setattr(settings, "database_url", None)
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "auth_attempts_per_window", 50)
    monkeypatch.setattr(
        settings,
        "bootstrap_token",
        SecretStr("test-bootstrap-token-long-enough-1234567890"),
    )

    old_password = "Admin-Password-Before-Rotation-42!"
    new_password = "Admin-Password-After-Rotation-84!"
    with TestClient(app) as admin_client:
        csrf = _csrf(admin_client)
        bootstrap = admin_client.post(
            "/api/auth/bootstrap",
            headers={"X-CSRF-Token": csrf},
            json={
                "email": "rotate-admin@example.test",
                "display_name": "Rotate Admin",
                "password": old_password,
                "bootstrap_token": "test-bootstrap-token-long-enough-1234567890",
            },
        )
        assert bootstrap.status_code == 200
        old_session_cookie = admin_client.cookies.get(settings.session_cookie_name)
        assert old_session_cookie

        with TestClient(app) as second_browser:
            second_browser.cookies.set(settings.session_cookie_name, old_session_cookie)
            assert second_browser.get("/api/auth/me").json()["authenticated"] is True

            no_csrf = admin_client.post(
                "/api/auth/password",
                json={"current_password": old_password, "new_password": new_password},
            )
            assert no_csrf.status_code == 403

            wrong_current = admin_client.post(
                "/api/auth/password",
                headers={"X-CSRF-Token": csrf},
                json={
                    "current_password": "Wrong-Current-Password-99!",
                    "new_password": new_password,
                },
            )
            assert wrong_current.status_code == 403

            changed = admin_client.post(
                "/api/auth/password",
                headers={"X-CSRF-Token": csrf},
                json={"current_password": old_password, "new_password": new_password},
            )
            assert changed.status_code == 200
            assert changed.json()["password_changed"] is True
            assert admin_client.cookies.get(settings.session_cookie_name) != old_session_cookie
            assert admin_client.get("/api/auth/me").json()["authenticated"] is True
            assert second_browser.get("/api/auth/me").json()["authenticated"] is False

            old_login_csrf = _csrf(second_browser)
            old_login = second_browser.post(
                "/api/auth/login",
                headers={"X-CSRF-Token": old_login_csrf},
                json={"email": "rotate-admin@example.test", "password": old_password},
            )
            assert old_login.status_code == 401

            new_login_csrf = _csrf(second_browser)
            new_login = second_browser.post(
                "/api/auth/login",
                headers={"X-CSRF-Token": new_login_csrf},
                json={"email": "rotate-admin@example.test", "password": new_password},
            )
            assert new_login.status_code == 200

        audit = admin_client.get("/api/admin/audit?limit=20")
        assert audit.status_code == 200
        events = [event for event in audit.json() if event["action"] == "auth.password.change"]
        assert {event["outcome"] for event in events} == {"failed", "success"}


def test_logout_revokes_server_session_and_clears_cookie(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "database_url", None)
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(
        settings,
        "bootstrap_token",
        SecretStr("test-bootstrap-token-long-enough-1234567890"),
    )

    with TestClient(app) as client:
        csrf = _csrf(client)
        bootstrap = client.post(
            "/api/auth/bootstrap",
            headers={"X-CSRF-Token": csrf},
            json={
                "email": "logout-admin@example.test",
                "display_name": "Logout Admin",
                "password": "Logout-Test-Password-42!",
                "bootstrap_token": "test-bootstrap-token-long-enough-1234567890",
            },
        )
        assert bootstrap.status_code == 200
        assert client.get("/api/auth/me").json()["authenticated"] is True
        assert settings.session_cookie_name in client.cookies

        logout = client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf})
        assert logout.status_code == 200
        assert logout.json()["logged_out"] is True
        assert settings.session_cookie_name not in client.cookies
        assert client.get("/api/auth/me").json()["authenticated"] is False

        events = client.get("/api/admin/audit?limit=20")
        assert events.status_code == 401
