from fastapi.testclient import TestClient
from pydantic import SecretStr

import nanou_cyber_ai.api as api_module
import nanou_cyber_ai.assistant.runtime as assistant_runtime
from nanou_cyber_ai.api import app
from nanou_cyber_ai.settings import settings


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_reports_local_database(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "database_url", None)
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    with TestClient(app) as client:
        response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["database"] == "sqlite"


def test_mcp_catalog_is_narrow() -> None:
    with TestClient(app) as client:
        response = client.get("/api/mcp/tools")
    assert response.status_code == 200
    names = {tool["name"] for tool in response.json()}
    assert "nvd.cve.get" in names
    assert "shell.exec" not in names
    assert "process.kill" not in names


def test_metadata_api_requires_signed_in_user(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "database_url", None)
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    with TestClient(app) as client:
        response = client.get("/api/malware/metadata")
    assert response.status_code == 401


def test_remote_developer_api_is_bearer_scoped_and_revocable(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "database_url", None)
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "auth_attempts_per_window", 50)
    monkeypatch.setattr(settings, "api_key_requests_per_minute", 60)
    monkeypatch.setattr(
        settings,
        "bootstrap_token",
        SecretStr("test-bootstrap-token-long-enough-1234567890"),
    )

    async def fake_kev_catalog(_client):
        return {"vulnerabilities": [{"cveID": "CVE-2024-0001"}]}

    monkeypatch.setattr(api_module, "fetch_kev_catalog", fake_kev_catalog)

    with TestClient(app) as admin_client:
        csrf = admin_client.get("/api/auth/csrf").json()["csrf_token"]
        bootstrap = admin_client.post(
            "/api/auth/bootstrap",
            headers={"X-CSRF-Token": csrf},
            json={
                "email": "developer-admin@example.test",
                "display_name": "Developer Admin",
                "password": "Developer-Admin-Strong-Password-42!",
                "bootstrap_token": "test-bootstrap-token-long-enough-1234567890",
            },
        )
        assert bootstrap.status_code == 200

        created = admin_client.post(
            "/api/developer/keys",
            headers={"X-CSRF-Token": csrf},
            json={
                "name": "AI threat-intelligence agent",
                "scopes": ["intel:read"],
                "expires_in_days": 30,
            },
        )
        assert created.status_code == 200
        token = created.json()["token"]
        key_id = created.json()["key"]["id"]
        assert token.startswith("ncd_live_")
        assert created.json()["shown_once"] is True
        assert "token_hash" not in created.json()["key"]

        listed = admin_client.get("/api/developer/keys")
        assert listed.status_code == 200
        assert listed.headers["cache-control"] == "no-store"
        assert len(listed.json()) == 1
        assert "token" not in listed.json()[0]
        assert "token_hash" not in listed.json()[0]

        with TestClient(app) as remote_client:
            missing = remote_client.get("/api/v1/kev")
            assert missing.status_code == 401
            headers = {"Authorization": f"Bearer {token}"}
            allowed = remote_client.get("/api/v1/kev", headers=headers)
            assert allowed.status_code == 200
            assert allowed.json()["vulnerabilities"][0]["cveID"] == "CVE-2024-0001"
            assert allowed.headers["cache-control"] == "no-store"

            denied_scope = remote_client.get(
                "/api/v1/malware/metadata",
                headers=headers,
            )
            assert denied_scope.status_code == 403

            schema = remote_client.get("/api/v1/openapi.json")
            assert schema.status_code == 200
            assert "NanouBearer" in schema.json()["components"]["securitySchemes"]
            assert "/api/v1/kev" in schema.json()["paths"]
            assert "/api/v1/cve/{cve_id}" in schema.json()["paths"]
            assert "/api/admin/users" not in schema.json()["paths"]

        revoked = admin_client.delete(
            f"/api/developer/keys/{key_id}",
            headers={"X-CSRF-Token": csrf},
        )
        assert revoked.status_code == 200
        assert revoked.json()["revoked"] is True

        with TestClient(app) as remote_client:
            after_revoke = remote_client.get(
                "/api/v1/kev",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert after_revoke.status_code == 401


def test_remote_api_rejects_expired_and_wrong_scope_keys(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "database_url", None)
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "auth_attempts_per_window", 50)
    monkeypatch.setattr(
        settings,
        "bootstrap_token",
        SecretStr("test-bootstrap-token-long-enough-1234567890"),
    )

    with TestClient(app) as admin_client:
        csrf = admin_client.get("/api/auth/csrf").json()["csrf_token"]
        bootstrap = admin_client.post(
            "/api/auth/bootstrap",
            headers={"X-CSRF-Token": csrf},
            json={
                "email": "scope-admin@example.test",
                "display_name": "Scope Admin",
                "password": "Scope-Admin-Strong-Password-42!",
                "bootstrap_token": "test-bootstrap-token-long-enough-1234567890",
            },
        )
        assert bootstrap.status_code == 200
        created = admin_client.post(
            "/api/developer/keys",
            headers={"X-CSRF-Token": csrf},
            json={
                "name": "Metadata-only key",
                "scopes": ["malware:metadata:read"],
                "expires_in_days": 1,
            },
        )
        assert created.status_code == 200
        token = created.json()["token"]

    with TestClient(app) as remote_client:
        headers = {"Authorization": f"Bearer {token}"}
        wrong_scope = remote_client.get("/api/v1/kev", headers=headers)
        assert wrong_scope.status_code == 403


def _bootstrap_api_admin(client: TestClient, email: str) -> str:
    csrf = client.get("/api/auth/csrf").json()["csrf_token"]
    response = client.post(
        "/api/auth/bootstrap",
        headers={"X-CSRF-Token": csrf},
        json={
            "email": email,
            "display_name": "Chat Admin",
            "password": "Chat-Admin-Strong-Password-42!",
            "bootstrap_token": "test-bootstrap-token-long-enough-1234567890",
        },
    )
    assert response.status_code == 200
    return csrf


def test_internal_chat_executes_read_only_command_and_records_audit(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "database_url", None)
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "auth_attempts_per_window", 50)
    monkeypatch.setattr(settings, "assistant_requests_per_minute", 30)
    monkeypatch.setattr(settings, "ai_api_key", None)
    monkeypatch.setattr(
        settings,
        "bootstrap_token",
        SecretStr("test-bootstrap-token-long-enough-1234567890"),
    )

    async def fake_kev_catalog(_client):
        return {
            "catalogVersion": "test-2026",
            "dateReleased": "2026-11-25",
            "vulnerabilities": [{"cveID": "CVE-2024-0001", "dateAdded": "2026-01-01"}],
        }

    monkeypatch.setattr(assistant_runtime, "fetch_kev_catalog", fake_kev_catalog)
    with TestClient(app) as client:
        csrf = _bootstrap_api_admin(client, "chat-admin@example.test")
        response = client.post(
            "/api/chat/command",
            headers={"X-CSRF-Token": csrf},
            json={"message": "Jereo CISA KEV"},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["mode"] == "local"
        assert result["action"] == "get_kev_summary"
        assert result["executed"] is True
        assert result["data"]["total_vulnerabilities"] == 1
        audit = client.get("/api/admin/audit?limit=20")
        assert audit.status_code == 200
        assert any(event["action"] == "assistant.command" for event in audit.json())


def test_remote_chat_requires_ai_chat_scope_and_runs_without_csrf(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "database_url", None)
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "auth_attempts_per_window", 50)
    monkeypatch.setattr(settings, "assistant_requests_per_minute", 30)
    monkeypatch.setattr(settings, "ai_api_key", None)
    monkeypatch.setattr(
        settings,
        "bootstrap_token",
        SecretStr("test-bootstrap-token-long-enough-1234567890"),
    )

    async def fake_kev_catalog(_client):
        return {"catalogVersion": "remote-test", "vulnerabilities": []}

    monkeypatch.setattr(assistant_runtime, "fetch_kev_catalog", fake_kev_catalog)
    with TestClient(app) as admin_client:
        csrf = _bootstrap_api_admin(admin_client, "remote-chat-admin@example.test")
        read_only_key = admin_client.post(
            "/api/developer/keys",
            headers={"X-CSRF-Token": csrf},
            json={
                "name": "Read-only key without chat",
                "scopes": ["intel:read"],
                "expires_in_days": 7,
            },
        )
        chat_key = admin_client.post(
            "/api/developer/keys",
            headers={"X-CSRF-Token": csrf},
            json={
                "name": "Remote AI assistant",
                "scopes": ["ai:chat", "intel:read"],
                "expires_in_days": 7,
            },
        )
        assert read_only_key.status_code == 200
        assert chat_key.status_code == 200

    with TestClient(app) as remote_client:
        denied = remote_client.post(
            "/api/v1/assistant/chat",
            headers={"Authorization": f"Bearer {read_only_key.json()['token']}"},
            json={"message": "Jereo CISA KEV"},
        )
        assert denied.status_code == 403

        allowed = remote_client.post(
            "/api/v1/assistant/chat",
            headers={"Authorization": f"Bearer {chat_key.json()['token']}"},
            json={"message": "Jereo CISA KEV"},
        )
        assert allowed.status_code == 200
        assert allowed.json()["action"] == "get_kev_summary"
        assert allowed.json()["executed"] is True
        assert allowed.headers["cache-control"] == "no-store"


def test_chat_requires_authenticated_session_and_valid_input(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "database_url", None)
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    with TestClient(app) as client:
        csrf = client.get("/api/auth/csrf").json()["csrf_token"]
        unauthenticated = client.post(
            "/api/chat/command",
            headers={"X-CSRF-Token": csrf},
            json={"message": "Jereo CISA KEV"},
        )
    assert unauthenticated.status_code == 401
