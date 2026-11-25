from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from nanou_cyber_ai.api import app
from nanou_cyber_ai.models import AttackSimulationIn
from nanou_cyber_ai.settings import settings
from nanou_cyber_ai.simulation import allowed_target_ids, run_offline_simulation


def _bootstrap_admin(client: TestClient) -> str:
    csrf = client.get("/api/auth/csrf").json()["csrf_token"]
    response = client.post(
        "/api/auth/bootstrap",
        headers={"X-CSRF-Token": csrf},
        json={
            "email": "simulation-admin@example.test",
            "display_name": "Simulation Admin",
            "password": "Simulation-Admin-Strong-Password-42!",
            "bootstrap_token": "simulation-bootstrap-token-long-enough-12345",
        },
    )
    assert response.status_code == 200
    return csrf


def test_allowed_targets_accept_only_opaque_lab_ids() -> None:
    assert allowed_target_ids("local-lab, Staging_Web, staging-web, https://example.test, 192.0.2.1") == [
        "local-lab",
        "staging-web",
    ]


def test_simulation_request_rejects_unknown_fields_and_bad_scope() -> None:
    try:
        AttackSimulationIn(
            target_id="https://example.test",
            profile="web_security",
            intensity="high",
            authorization_reference="CHANGE-123",
            authorization_acknowledged=True,
        )
    except ValidationError:
        pass
    else:
        raise AssertionError("Unsafe target and intensity must be rejected.")


def test_offline_simulation_is_synthetic_and_never_contacts_target(monkeypatch) -> None:
    monkeypatch.setattr(settings, "simulation_allowed_targets", "local-lab,staging")
    item = AttackSimulationIn(
        target_id="local-lab",
        profile="api_security",
        intensity="medium",
        authorization_reference="CHANGE-2026-014",
        authorization_acknowledged=True,
    )
    result = run_offline_simulation(item, configured_targets=settings.simulation_allowed_targets)

    assert result["status"] == "SIMULATED"
    assert result["network_activity"] is False
    assert result["target_contacted"] is False
    assert result["commands_executed"] is False
    assert result["credentials_accessed"] is False
    assert result["malware_executed"] is False
    assert result["events_generated"] == 3
    assert all(event["is_synthetic"] for event in result["events"])
    assert {event["source"] for event in result["events"]} == {"NANOU_SYNTHETIC_TELEMETRY"}


def test_simulation_requires_authorization_and_allowlisted_target(monkeypatch) -> None:
    monkeypatch.setattr(settings, "simulation_allowed_targets", "local-lab")
    unconfirmed = AttackSimulationIn(
        target_id="local-lab",
        profile="reconnaissance",
        intensity="passive",
        authorization_reference="CHANGE-2026-015",
        authorization_acknowledged=False,
    )
    with pytest.raises(PermissionError):
        run_offline_simulation(unconfirmed, configured_targets=settings.simulation_allowed_targets)

    unlisted = AttackSimulationIn(
        target_id="outside-lab",
        profile="reconnaissance",
        intensity="passive",
        authorization_reference="CHANGE-2026-016",
        authorization_acknowledged=True,
    )
    with pytest.raises(PermissionError):
        run_offline_simulation(unlisted, configured_targets=settings.simulation_allowed_targets)


def test_simulation_routes_are_session_protected_and_audited(monkeypatch, tmp_path) -> None:
    import pytest
    from pydantic import SecretStr

    monkeypatch.setattr(settings, "database_url", None)
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "auth_attempts_per_window", 50)
    monkeypatch.setattr(settings, "simulation_requests_per_hour", 10)
    monkeypatch.setattr(settings, "simulation_allowed_targets", "local-lab,staging")
    monkeypatch.setattr(
        settings,
        "bootstrap_token",
        SecretStr("simulation-bootstrap-token-long-enough-12345"),
    )

    with TestClient(app) as client:
        unauthenticated = client.get("/api/simulations/config")
        assert unauthenticated.status_code == 401

        csrf = _bootstrap_admin(client)
        config = client.get("/api/simulations/config")
        assert config.status_code == 200
        assert config.json()["mode"] == "offline_synthetic_only"
        assert [item["id"] for item in config.json()["targets"]] == ["local-lab", "staging"]
        assert config.json()["controls"]["network_activity"] is False

        payload = {
            "target_id": "local-lab",
            "profile": "web_security",
            "intensity": "low",
            "authorization_reference": "CHANGE-2026-017",
            "authorization_acknowledged": True,
        }
        result = client.post(
            "/api/simulations/run",
            headers={"X-CSRF-Token": csrf},
            json=payload,
        )
        assert result.status_code == 200
        assert result.json()["target_contacted"] is False
        assert result.json()["events_generated"] == 2

        denied = client.post(
            "/api/simulations/run",
            headers={"X-CSRF-Token": csrf},
            json={**payload, "authorization_acknowledged": False},
        )
        assert denied.status_code == 403

        audit = client.get("/api/admin/audit?limit=30")
        assert audit.status_code == 200
        events = audit.json()
        assert any(event["action"] == "attack_simulation.run" and event["outcome"] == "simulated" for event in events)
        assert any(event["action"] == "attack_simulation.run" and event["outcome"] == "blocked" for event in events)

    with pytest.raises(ValidationError):
        AttackSimulationIn(
            target_id="local-lab",
            profile="authentication",
            intensity="extreme",
            authorization_reference="CHANGE-2026-018",
            authorization_acknowledged=True,
        )


def test_simulation_ui_is_scoped_and_uses_local_assets() -> None:
    with TestClient(app) as client:
        home = client.get("/")
        script = client.get("/assets/simulation.js")
        stylesheet = client.get("/assets/simulation.css")

    assert home.status_code == 200
    assert 'id="attack-simulation"' in home.text
    assert 'id="simulation-form"' in home.text
    assert 'data-role-visibility="admin,analyst"' in home.text
    assert script.status_code == 200
    assert "apiRequest(\"/api/simulations/run\"" in script.text
    assert "localStorage" not in script.text
    assert "textContent" in script.text
    assert stylesheet.status_code == 200
    assert ".simulation-panel" in stylesheet.text
