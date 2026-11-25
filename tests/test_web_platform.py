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
    assert '<meta name="theme-color" content="#050505">' in response.text


def test_dark_soc_styles_include_responsive_and_reduced_motion_support() -> None:
    with TestClient(app) as client:
        response = client.get("/assets/app.css")

    assert response.status_code == 200
    assert "--bg: #050505" in response.text
    assert "--sidebar: #080808" in response.text
    assert "--panel: #101010" in response.text
    assert "Pure-black executive SOC theme" in response.text
    assert "background: #050505" in response.text
    assert "background: #080808" in response.text
    assert ".nav-group-label" in response.text
    assert ".theme-pill" in response.text
    assert "@media (max-width: 760px)" in response.text
    assert "@media (prefers-reduced-motion: reduce)" in response.text


def test_role_based_workspace_and_navigation_are_scoped_by_role() -> None:
    with TestClient(app) as client:
        home = client.get("/")
        script = client.get("/assets/app.js")

    assert home.status_code == 200
    assert 'id="role-workspace" data-role-visibility="authenticated"' in home.text
    assert 'data-role-visibility="admin,analyst"' in home.text
    assert 'data-role-visibility="admin"' in home.text
    assert 'data-role-visibility="authenticated"' in home.text
    assert 'id="metadata-write-access"' in home.text
    assert 'id="malware-analysis-panel"' in home.text

    assert script.status_code == 200
    assert "const ROLE_WORKSPACES = {" in script.text
    assert "admin: {" in script.text
    assert "analyst: {" in script.text
    assert "viewer: {" in script.text
    assert "function updateRoleVisibility()" in script.text
    assert "function renderRoleWorkspace()" in script.text
    assert 'byId("metadata-create-form").hidden = !canWriteMetadata;' in script.text


def test_role_workspace_styles_remain_responsive_in_black_theme() -> None:
    with TestClient(app) as client:
        response = client.get("/assets/app.css")

    assert response.status_code == 200
    assert ".role-workspace" in response.text
    assert ".role-permissions" in response.text
    assert ".role-permission" in response.text
    assert ".access-note" in response.text
    assert "grid-template-columns: repeat(3, minmax(0, 1fr))" in response.text
    assert "@media (max-width: 760px)" in response.text
    assert ".nav-group[hidden]" in response.text


def test_admin_workspace_has_account_and_audit_filters() -> None:
    with TestClient(app) as client:
        home = client.get("/")
        script = client.get("/assets/app.js")
        stylesheet = client.get("/assets/app.css")

    assert home.status_code == 200
    assert 'id="admin-total-users"' in home.text
    assert 'id="admin-pending-users"' in home.text
    assert 'id="admin-user-search"' in home.text
    assert 'id="admin-user-filter"' in home.text
    assert 'id="audit-search"' in home.text
    assert 'id="audit-outcome-filter"' in home.text

    assert script.status_code == 200
    assert "function adminUserState(item)" in script.text
    assert "function formatAuditDate(value)" in script.text
    assert "function auditOutcomeLabel(value)" in script.text
    assert 'apiRequest("/api/admin/audit?limit=100")' in script.text
    assert 'addEventListener("input", () => renderAdminUsers(adminUsersCache))' in script.text
    assert 'addEventListener("input", () => renderAudit(adminAuditCache))' in script.text

    assert stylesheet.status_code == 200
    assert ".admin-summary" in stylesheet.text
    assert ".admin-toolbar" in stylesheet.text
    assert ".audit-toolbar" in stylesheet.text
    assert ".audit-outcome" in stylesheet.text
    assert "@media (max-width: 760px)" in stylesheet.text
