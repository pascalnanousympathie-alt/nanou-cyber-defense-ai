from fastapi.testclient import TestClient

from nanou_cyber_ai.api import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_mcp_catalog_is_narrow() -> None:
    with TestClient(app) as client:
        response = client.get("/api/mcp/tools")
    assert response.status_code == 200
    names = {tool["name"] for tool in response.json()}
    assert "nvd.cve.get" in names
    assert "shell.exec" not in names
    assert "process.kill" not in names


def test_metadata_api_disabled_without_token() -> None:
    with TestClient(app) as client:
        response = client.get("/api/malware/metadata")
    assert response.status_code == 503
