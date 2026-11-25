from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError
from sqlalchemy import update

from nanou_cyber_ai.attack_simulation import build_simulation_report
from nanou_cyber_ai.api import app
from nanou_cyber_ai.models import AttackScopeCreateIn, AttackSimulationCreateIn
from nanou_cyber_ai.settings import settings
from nanou_cyber_ai.storage.database import attack_scopes, get_database


def _scope_input(**overrides) -> dict:
    payload = {
        "name": "Approved Lab",
        "target": "lab.example.test",
        "authorization_basis": "isolated_lab",
        "authorization_expires_on": (datetime.now(UTC).date() + timedelta(days=30)).isoformat(),
        "authorization_confirmed": True,
    }
    payload.update(overrides)
    return payload


def test_attack_scope_requires_authorization_and_single_host_target() -> None:
    scope = AttackScopeCreateIn(**_scope_input(target="  LAB.Example.Test. "))
    assert scope.target == "lab.example.test"

    ipv6 = AttackScopeCreateIn(**_scope_input(target="2001:db8::1"))
    assert ipv6.target == "2001:db8::1"

    with pytest.raises(ValidationError):
        AttackScopeCreateIn(**_scope_input(authorization_confirmed=False))
    with pytest.raises(ValidationError):
        AttackScopeCreateIn(**_scope_input(target="https://example.test/path"))
    with pytest.raises(ValidationError):
        AttackScopeCreateIn(**_scope_input(target="192.168.1.0/24"))
    with pytest.raises(ValidationError):
        AttackScopeCreateIn(**_scope_input(target="example.test:443"))
    with pytest.raises(ValidationError):
        AttackScopeCreateIn(**_scope_input(target="192.168.001.010"))
    with pytest.raises(ValidationError):
        AttackScopeCreateIn(**_scope_input(target="fe80::1%eth0"))
    with pytest.raises(ValidationError):
        AttackScopeCreateIn(
            **_scope_input(authorization_expires_on=(datetime.now(UTC).date() - timedelta(days=1)).isoformat())
        )


def test_attack_simulation_config_is_bounded_and_requires_confirmation() -> None:
    valid = AttackSimulationCreateIn(
        scope_id="a" * 32,
        profile="api_security",
        intensity="medium",
        duration_minutes=30,
        authorization_confirmed=True,
    )
    assert valid.profile == "api_security"

    with pytest.raises(ValidationError):
        AttackSimulationCreateIn(
            scope_id="a" * 32,
            profile="api_security",
            intensity="high",
            duration_minutes=10,
            authorization_confirmed=True,
        )
    with pytest.raises(ValidationError):
        AttackSimulationCreateIn(
            scope_id="a" * 32,
            profile="web_security",
            intensity="low",
            duration_minutes=31,
            authorization_confirmed=True,
        )
    with pytest.raises(ValidationError):
        AttackSimulationCreateIn(
            scope_id="a" * 32,
            profile="web_security",
            intensity="low",
            duration_minutes=10,
            authorization_confirmed=False,
        )


@pytest.mark.parametrize(
    ("intensity", "expected_checks"),
    [("passive", 3), ("low", 5), ("medium", 7)],
)
def test_simulation_report_is_local_and_never_claims_verified_findings(
    intensity: str,
    expected_checks: int,
) -> None:
    scope = {
        "id": "s" * 32,
        "name": "Test lab",
        "target": "lab.example.test",
        "target_type": "domain",
        "authorization_expires_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
    }
    report = build_simulation_report(
        simulation_id="r" * 32,
        scope=scope,
        profile="web_security",
        intensity=intensity,
        duration_minutes=10,
    )
    assert report["status"] == "simulation_only"
    assert report["execution"] == {
        "mode": "local_deterministic_tabletop",
        "network_requests": 0,
        "hosts_contacted": 0,
        "exploits_executed": 0,
        "payloads_executed": 0,
        "malware_executed": False,
        "automatic_changes": 0,
    }
    assert report["summary"]["verified_findings"] == 0
    assert len(report["checks"]) == expected_checks
    assert all(item["status"] == "requires_manual_validation" for item in report["checks"])
    assert all("Threat-reference mapping only" in item["usage"] for item in report["attack_mapping"])
    assert len(report["detection_recommendations"]) == 3
    assert all(
        "not a deployed" in item["type"]
        and item["status"] == "draft_only"
        and item["enabled"] is False
        for item in report["detection_recommendations"]
    )


def _bootstrap_admin(client: TestClient, email: str) -> str:
    csrf = client.get("/api/auth/csrf").json()["csrf_token"]
    response = client.post(
        "/api/auth/bootstrap",
        headers={"X-CSRF-Token": csrf},
        json={
            "email": email,
            "display_name": "Simulation Admin",
            "password": "Simulation-Admin-Strong-Password-42!",
            "bootstrap_token": "test-bootstrap-token-long-enough-1234567890",
        },
    )
    assert response.status_code == 200
    return csrf


def _create_analyst(admin_client: TestClient, csrf: str, email: str) -> tuple[TestClient, str]:
    registered = admin_client.post(
        "/api/auth/register",
        headers={"X-CSRF-Token": csrf},
        json={
            "email": email,
            "display_name": "Simulation Analyst",
            "password": "Simulation-Analyst-Strong-Password-42!",
        },
    )
    assert registered.status_code == 202
    users = admin_client.get("/api/admin/users").json()
    analyst = next(item for item in users if item["email"] == email)
    updated = admin_client.patch(
        f"/api/admin/users/{analyst['id']}",
        headers={"X-CSRF-Token": csrf},
        json={"role": "analyst", "is_active": True},
    )
    assert updated.status_code == 200

    client = TestClient(app)
    analyst_csrf = client.get("/api/auth/csrf").json()["csrf_token"]
    login = client.post(
        "/api/auth/login",
        headers={"X-CSRF-Token": analyst_csrf},
        json={
            "email": email,
            "password": "Simulation-Analyst-Strong-Password-42!",
        },
    )
    assert login.status_code == 200
    return client, analyst_csrf


def test_attack_simulation_api_enforces_roles_scope_and_audit(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "database_url", None)
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "auth_attempts_per_window", 50)
    monkeypatch.setattr(settings, "attack_scope_creations_per_day", 20)
    monkeypatch.setattr(settings, "attack_simulations_per_hour", 8)
    monkeypatch.setattr(
        settings,
        "bootstrap_token",
        SecretStr("test-bootstrap-token-long-enough-1234567890"),
    )

    with TestClient(app) as admin_client:
        csrf = _bootstrap_admin(admin_client, "simulation-admin@example.test")
        missing_csrf = admin_client.post(
            "/api/attack/scopes",
            json=_scope_input(name="Missing CSRF"),
        )
        assert missing_csrf.status_code == 403

        scope_response = admin_client.post(
            "/api/attack/scopes",
            headers={"X-CSRF-Token": csrf},
            json=_scope_input(),
        )
        assert scope_response.status_code == 201
        scope = scope_response.json()
        assert scope["target"] == "lab.example.test"
        assert scope["is_authorization_current"] is True

        analyst_client, analyst_csrf = _create_analyst(
            admin_client,
            csrf,
            "simulation-analyst@example.test",
        )
        with analyst_client:
            scopes = analyst_client.get("/api/attack/scopes")
            assert scopes.status_code == 200
            assert scopes.json()[0]["id"] == scope["id"]

            denied_scope_write = analyst_client.post(
                "/api/attack/scopes",
                headers={"X-CSRF-Token": analyst_csrf},
                json=_scope_input(name="Analyst cannot add"),
            )
            assert denied_scope_write.status_code == 403

            simulation = analyst_client.post(
                "/api/attack/simulations",
                headers={"X-CSRF-Token": analyst_csrf},
                json={
                    "scope_id": scope["id"],
                    "profile": "api_security",
                    "intensity": "medium",
                    "duration_minutes": 12,
                    "authorization_confirmed": True,
                },
            )
            assert simulation.status_code == 201
            report = simulation.json()
            assert report["execution"]["network_requests"] == 0
            assert report["execution"]["exploits_executed"] == 0
            assert report["summary"]["checks_prepared"] == 7
            assert report["summary"]["verified_findings"] == 0

            history = analyst_client.get("/api/attack/simulations")
            assert history.status_code == 200
            assert history.json()[0]["id"] == report["id"]

        revoked = admin_client.post(
            f"/api/attack/scopes/{scope['id']}/revoke",
            headers={"X-CSRF-Token": csrf},
            json={},
        )
        assert revoked.status_code == 200
        assert revoked.json()["revoked"] is True

        with analyst_client:
            denied = analyst_client.post(
                "/api/attack/simulations",
                headers={"X-CSRF-Token": analyst_csrf},
                json={
                    "scope_id": scope["id"],
                    "profile": "reconnaissance",
                    "intensity": "passive",
                    "duration_minutes": 5,
                    "authorization_confirmed": True,
                },
            )
            assert denied.status_code == 409

        audit = admin_client.get("/api/admin/audit?limit=50")
        assert audit.status_code == 200
        actions = {item["action"] for item in audit.json()}
        assert "attack.scope.create" in actions
        assert "attack.simulation.create" in actions
        assert "attack.scope.revoke" in actions
        assert "attack.simulation.scope_blocked" in actions


def test_attack_scope_expiry_is_rechecked_at_execution(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "database_url", None)
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(
        settings,
        "bootstrap_token",
        SecretStr("test-bootstrap-token-long-enough-1234567890"),
    )
    with TestClient(app) as client:
        csrf = _bootstrap_admin(client, "expiry-admin@example.test")
        created = client.post(
            "/api/attack/scopes",
            headers={"X-CSRF-Token": csrf},
            json=_scope_input(name="Expiry lab"),
        )
        assert created.status_code == 201
        scope_id = created.json()["id"]

        database = get_database(None, tmp_path)
        with database.engine.begin() as connection:
            connection.execute(
                update(attack_scopes)
                .where(attack_scopes.c.id == scope_id)
                .values(
                    authorization_expires_at=datetime.now(UTC) - timedelta(minutes=1)
                )
            )

        response = client.post(
            "/api/attack/simulations",
            headers={"X-CSRF-Token": csrf},
            json={
                "scope_id": scope_id,
                "profile": "authentication",
                "intensity": "low",
                "duration_minutes": 10,
                "authorization_confirmed": True,
            },
        )
        assert response.status_code == 409
        assert "Lany daty" in response.json()["detail"]


def test_attack_endpoints_require_authenticated_analyst_or_admin() -> None:
    with TestClient(app) as client:
        response = client.get("/api/attack/scopes")
        assert response.status_code == 401
        run = client.get("/api/attack/simulations")
        assert run.status_code == 401
