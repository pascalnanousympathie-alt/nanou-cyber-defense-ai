from fastapi.testclient import TestClient

from nanou_cyber_ai.api import app


def test_web_platform_serves_home_page_and_assets() -> None:
    with TestClient(app) as client:
        home = client.get("/")
        stylesheet = client.get("/assets/app.css")
        script = client.get("/assets/app.js")

    assert home.status_code == 200
    assert "text/html" in home.headers["content-type"]
    assert "Nanou Cyber Defense AI" in home.text
    assert stylesheet.status_code == 200
    assert "text/css" in stylesheet.headers["content-type"]
    assert script.status_code == 200
    assert "javascript" in script.headers["content-type"]


def test_web_platform_uses_restrictive_security_headers() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "script-src 'self'" in response.headers["content-security-policy"]
    assert "style-src 'self'" in response.headers["content-security-policy"]
    assert "object-src 'none'" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-store"


def test_admin_bootstrap_form_has_private_token_field() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert 'id="bootstrap-token"' in response.text
    assert 'id="bootstrap-password"' in response.text
