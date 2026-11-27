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
    policy = response.headers["content-security-policy"]
    assert "script-src 'self' https://accounts.google.com/gsi/client" in policy
    assert "frame-src https://accounts.google.com/gsi/" in policy
    assert "connect-src 'self' https://accounts.google.com/gsi/" in policy
    assert "style-src 'self'" in policy
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
    assert 'data-category-target="home">' in response.text
    assert 'data-category-target="threat">' in response.text
    assert 'data-category-target="malware">' in response.text
    assert 'data-category-target="assistant">' in response.text
    assert 'data-category-target="operations" data-role-visibility="admin,analyst"' in response.text
    assert 'data-category-target="account">' in response.text
    assert 'data-category-view="threat"' in response.text
    assert 'data-category-view="malware"' in response.text
    assert 'data-category-view="assistant"' in response.text
    assert 'data-category-view="operations"' in response.text
    assert 'data-category-view="account"' in response.text
    assert "Tabletop simulation" in response.text
    assert "AI Chat Command Center" in response.text
    assert 'href="#vulnerabilities"' in response.text
    assert 'href="#malware-model"' in response.text
    assert 'href="#metadata"' in response.text
    assert 'href="#tools"' in response.text
    assert 'class="theme-pill"' in response.text
    assert '<meta name="theme-color" content="#03070b">' in response.text


def test_dark_soc_styles_include_responsive_and_reduced_motion_support() -> None:
    with TestClient(app) as client:
        response = client.get("/assets/app.css")

    assert response.status_code == 200
    assert "--bg: #03070b" in response.text
    assert "--sidebar: #050b11" in response.text
    assert "--panel: #08121a" in response.text
    assert "Neon cyber operations theme" in response.text
    assert "background: #03070b" in response.text
    assert "linear-gradient(180deg, rgba(5,12,17,.99)" in response.text
    assert ".nav-group-label" in response.text
    assert ".theme-pill" in response.text
    assert "text-shadow:" in response.text
    assert "transform-style: preserve-3d" in response.text
    assert "Neon cyber operations theme" in response.text
    assert "@media (max-width: 760px)" in response.text
    assert "@media (prefers-reduced-motion: reduce)" in response.text


def test_role_based_workspace_and_navigation_are_scoped_by_role() -> None:
    with TestClient(app) as client:
        home = client.get("/")
        script = client.get("/assets/app.js")

    assert home.status_code == 200
    assert (
        'id="role-workspace" data-category-view="account" '
        'data-role-visibility="authenticated"'
    ) in home.text
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


def test_developer_center_assets_and_read_only_integration_contract() -> None:
    with TestClient(app) as client:
        home = client.get("/")
        script = client.get("/assets/developer.js")
        stylesheet = client.get("/assets/developer.css")
        schema = client.get("/api/v1/openapi.json")

    assert home.status_code == 200
    assert 'href="/assets/developer.css"' in home.text
    assert 'src="/assets/developer.js"' in home.text
    assert 'id="developer"' in home.text
    assert 'id="developer-key-form"' in home.text
    assert 'id="developer-key-once"' in home.text

    assert script.status_code == 200
    assert "function createDeveloperKey(event)" in script.text
    assert "function revokeDeveloperKey(keyId, button)" in script.text
    assert "navigator.clipboard.writeText" in script.text
    assert "localStorage" not in script.text

    assert stylesheet.status_code == 200
    assert ".developer-panel" in stylesheet.text
    assert ".developer-key-status" in stylesheet.text
    assert "@media(max-width:760px)" in stylesheet.text

    assert schema.status_code == 200
    document = schema.json()
    assert document["openapi"] == "3.1.0"
    assert "NanouBearer" in document["components"]["securitySchemes"]
    assert set(document["paths"]) == {
        "/api/v1/kev",
        "/api/v1/cve/{cve_id}",
        "/api/v1/malware/metadata",
        "/api/v1/assistant/chat",
    }
    assert "AssistantChatRequest" in document["components"]["schemas"]
    for path_item in document["paths"].values():
        for operation in path_item.values():
            assert "security" in operation


def test_attack_simulation_manager_assets_and_local_only_contract() -> None:
    with TestClient(app) as client:
        home = client.get("/")
        script = client.get("/assets/attack-simulation.js")
        stylesheet = client.get("/assets/attack-simulation.css")

    assert home.status_code == 200
    assert (
        'href="#attack-simulation" data-category-target="operations" '
        'data-role-visibility="admin,analyst"'
    ) in home.text
    assert 'id="attack-manager-panel"' in home.text
    assert 'id="attack-scope-form"' in home.text
    assert 'id="attack-run-form"' in home.text
    assert 'id="attack-scope-confirm"' in home.text
    assert 'id="attack-run-confirm"' in home.text
    assert "SOC detection rules" in home.text
    assert "0 network requests" in home.text

    assert script.status_code == 200
    assert 'apiRequest("/api/attack/scopes")' in script.text
    assert 'apiRequest("/api/attack/simulations?limit=30")' in script.text
    assert "textContent" in script.text
    assert "detection_recommendations" in script.text
    assert "innerHTML" not in script.text
    assert "localStorage" not in script.text

    assert stylesheet.status_code == 200
    assert ".attack-manager-panel" in stylesheet.text
    assert ".attack-safety-banner" in stylesheet.text
    assert "@media(max-width:760px)" in stylesheet.text


def test_assistant_chat_assets_and_command_policy_are_present() -> None:
    with TestClient(app) as client:
        home = client.get("/")
        script = client.get("/assets/assistant.js")
        stylesheet = client.get("/assets/assistant.css")
        schema = client.get("/api/v1/openapi.json")

    assert home.status_code == 200
    assert 'id="assistant-chat"' in home.text
    assert 'id="assistant-chat-form"' in home.text
    assert 'data-assistant-command="Jereo CISA KEV"' in home.text
    assert 'data-assistant-command="Attack simulation help"' in home.text
    assert 'href="/assets/assistant.css"' in home.text
    assert 'src="/assets/assistant.js"' in home.text

    assert script.status_code == 200
    assert 'apiRequest("/api/chat/command"' in script.text
    assert 'result.action === "attack_simulation_help"' in script.text
    assert 'managerLink.href = "#attack-simulation"' in script.text
    assert 'textContent = "Sokafy ny Attack Simulation Manager' in script.text
    assert "localStorage" not in script.text
    assert "textContent = content" in script.text

    assert stylesheet.status_code == 200
    assert ".assistant-chat-log" in stylesheet.text
    assert ".assistant-message" in stylesheet.text
    assert "@media(max-width:760px)" in stylesheet.text

    assert schema.status_code == 200
    operation = schema.json()["paths"]["/api/v1/assistant/chat"]["post"]
    assert operation["requestBody"]["required"] is True
    request_ref = operation["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    assert "AssistantChatRequest" in request_ref


def test_account_workspace_exposes_safe_password_rotation_form() -> None:
    with TestClient(app) as client:
        home = client.get("/")
        script = client.get("/assets/app.js")

    assert home.status_code == 200
    assert 'id="password-change-form"' in home.text
    assert 'id="current-password"' in home.text
    assert 'id="new-password"' in home.text
    assert 'id="confirm-password"' in home.text
    assert 'autocomplete="current-password"' in home.text
    assert 'autocomplete="new-password"' in home.text

    assert script.status_code == 200
    assert 'apiRequest("/api/auth/password"' in script.text
    assert (
        'byId("password-change-form").addEventListener("submit", submitPasswordChange)'
        in script.text
    )
    assert "localStorage" not in script.text


def test_request_body_limit_rejects_oversized_content_length() -> None:
    oversized_body = b"x" * (2 * 1024 * 1024 + 1)
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            content=oversized_body,
            headers={"Content-Type": "application/json"},
        )

    assert response.status_code == 413


def test_request_body_limit_rejects_chunked_body_without_content_length() -> None:
    def chunks():
        yield b'{"email":"large@example.test","password":"'
        yield b"x" * (2 * 1024 * 1024)
        yield b'"}'

    with TestClient(app) as client:
        csrf = client.get("/api/auth/csrf").json()["csrf_token"]
        response = client.post(
            "/api/auth/login",
            content=chunks(),
            headers={"Content-Type": "application/json", "X-CSRF-Token": csrf},
        )

    assert response.status_code == 413, response.text


def test_login_first_google_signup_link_and_category_home_are_served() -> None:
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert '<body data-auth-state="checking">' in response.text
    assert 'id="login-form"' in response.text
    assert 'id="google-button-slot"' in response.text
    assert 'id="register-open-link"' in response.text
    assert 'id="register-form" class="auth-form" hidden' in response.text
    assert 'id="category-home" class="category-home" hidden' in response.text
    assert 'data-open-category="threat"' in response.text
    assert 'data-open-category="malware"' in response.text
    assert 'data-open-category="assistant"' in response.text
    assert 'data-category-view="operations"' in response.text
