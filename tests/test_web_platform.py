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


def test_home_groups_navigation_and_defaults_to_dark_soc_theme() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert '<html lang="mg" data-theme="dark">' in response.text
    assert 'aria-label="Navigation principale"' in response.text
    assert 'class="nav-group-label">Threat intelligence</span>' in response.text
    assert 'class="nav-group-label">Malware laboratory</span>' in response.text
    assert 'class="nav-group-label">Accès &amp; gouvernance</span>' in response.text
    assert 'href="#vulnerabilities"' in response.text
    assert 'href="#kev"' in response.text
    assert 'href="#malware-model"' in response.text
    assert 'href="#metadata"' in response.text
    assert 'href="#tools"' in response.text
    assert 'class="theme-pill"' in response.text


def test_dark_soc_styles_include_responsive_and_reduced_motion_support() -> None:
    with TestClient(app) as client:
        response = client.get("/assets/app.css")

    assert response.status_code == 200
    assert "--bg: #070d18" in response.text
    assert ".nav-group-label" in response.text
    assert ".theme-pill" in response.text
    assert "@media (max-width: 760px)" in response.text
    assert "@media (prefers-reduced-motion: reduce)" in response.text
