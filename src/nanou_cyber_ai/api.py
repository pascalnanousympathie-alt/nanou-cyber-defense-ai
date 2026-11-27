"""FastAPI application for the Nanou Cyber Defense web platform."""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated
from urllib.parse import urlsplit

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from nanou_cyber_ai.assistant.runtime import run_assistant
from nanou_cyber_ai.connectors.kev import fetch_kev_catalog
from nanou_cyber_ai.connectors.nvd import fetch_cve
from nanou_cyber_ai.malware.feature_csv import prepare_feature_csv
from nanou_cyber_ai.malware.inference import classify_features, load_verified_model
from nanou_cyber_ai.mcp.registry import list_tools
from nanou_cyber_ai.models import (
    AdminPairingExchangeIn,
    AdminUserUpdateIn,
    AssistantChatIn,
    AttackScopeCreateIn,
    AttackSimulationCreateIn,
    AuthBootstrapIn,
    AuthLoginIn,
    AuthPasswordChangeIn,
    AuthRegisterIn,
    DeveloperApiKeyCreateIn,
    GoogleSignInIn,
    MalwareInferenceIn,
    MalwareInferenceResult,
    MalwareMetadata,
    MalwareMetadataIn,
)
from nanou_cyber_ai.security.passwords import hash_password, verify_password
from nanou_cyber_ai.settings import settings
from nanou_cyber_ai.storage.attack_simulation import AttackSimulationStore
from nanou_cyber_ai.storage.auth import (
    ADMIN_BRIDGE_TTL_SECONDS,
    ADMIN_PAIRING_TTL_SECONDS,
    AuthStore,
)
from nanou_cyber_ai.storage.database import SecurityDatabase, get_database
from nanou_cyber_ai.storage.sqlite import MalwareMetadataStore

app = FastAPI(
    title="Nanou Cyber Defense AI",
    version="0.2.0",
    description="Defensive vulnerability intelligence and malware feature analysis.",
)
_WEB_DIR = Path(__file__).resolve().parent / "web"
_CSRF_COOKIE = "nanou_csrf"
_MAX_REQUEST_BYTES = 2 * 1024 * 1024
_LOCAL_AUDIT_HMAC_KEY = secrets.token_bytes(32)
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


app.mount("/assets", StaticFiles(directory=_WEB_DIR / "assets"), name="web-assets")


def get_database_instance() -> SecurityDatabase:
    configured_database_url = settings.effective_database_url
    database_url = (
        configured_database_url.get_secret_value() if configured_database_url is not None else None
    )
    try:
        return get_database(database_url, settings.data_dir)
    except (RuntimeError, ValueError, OSError, SQLAlchemyError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Persistent database is not configured or is temporarily unavailable.",
        ) from exc


def get_auth_store() -> AuthStore:
    return AuthStore(get_database_instance())


def get_store() -> MalwareMetadataStore:
    return MalwareMetadataStore(get_database_instance())


def get_attack_store() -> AttackSimulationStore:
    return AttackSimulationStore(get_database_instance())


def _request_id(request: Request) -> str:
    supplied = request.headers.get("x-request-id", "").strip()
    if supplied and len(supplied) <= 80 and all(ch.isalnum() or ch in "-_." for ch in supplied):
        return supplied
    return uuid.uuid4().hex


def _audit_hmac_key() -> bytes:
    configured = settings.audit_hmac_key
    if configured is not None:
        return configured.get_secret_value().encode("utf-8")

    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        raise RuntimeError("NANOU_AUDIT_HMAC_KEY is required on serverless hosting.")

    # Local development only: a process-local key avoids storing recoverable PII.
    return _LOCAL_AUDIT_HMAC_KEY


def _hmac_fingerprint(purpose: str, value: str) -> str:
    message = f"{purpose}:{value}".encode()
    return hmac.new(_audit_hmac_key(), message, hashlib.sha256).hexdigest()


def _ip_digest(request: Request) -> str | None:
    # Use the direct peer address; do not trust arbitrary X-Forwarded-For input.
    peer = request.client.host if request.client else None
    return _hmac_fingerprint("audit-ip", peer) if peer else None


def _rate_fingerprints(request: Request, email: str, action: str) -> tuple[str, str | None]:
    normalized_email = email.strip().lower()
    email_digest = _hmac_fingerprint(f"rate-email:{action}", normalized_email)
    peer = request.client.host if request.client else None
    ip_digest = _hmac_fingerprint(f"rate-ip:{action}", peer) if peer else None
    return email_digest, ip_digest


def _check_rate_limit(store: AuthStore, request: Request, email: str, action: str) -> None:
    email_fingerprint, ip_fingerprint = _rate_fingerprints(request, email, action)
    allowed = store.allow_attempt(
        email_fingerprint,
        maximum=settings.auth_attempts_per_window,
        window_seconds=settings.auth_rate_window_seconds,
    )
    if ip_fingerprint:
        allowed = (
            store.allow_attempt(
                ip_fingerprint,
                maximum=settings.auth_attempts_per_window * 4,
                window_seconds=settings.auth_rate_window_seconds,
            )
            and allowed
        )
    if not allowed:
        store.record_event(
            actor_user_id=None,
            action=f"{action}.rate_limited",
            outcome="blocked",
            request_id=_request_id(request),
            ip_digest=_ip_digest(request),
        )
        raise HTTPException(
            status_code=429,
            detail="Too many authentication attempts. Try again later.",
        )


def _session_token(request: Request, response: Response, store: AuthStore, user_id: str) -> None:
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(UTC) + timedelta(hours=settings.session_ttl_hours)
    store.create_session(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=raw_token,
        max_age=settings.session_ttl_hours * 3600,
        expires=expires_at,
        path="/",
        secure=request.url.scheme == "https",
        httponly=True,
        samesite="strict",
    )


def _clear_session_cookie(request: Request, response: Response) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=request.url.scheme == "https",
        httponly=True,
        samesite="strict",
    )


def _current_user(request: Request) -> dict | None:
    raw_token = request.cookies.get(settings.session_cookie_name)
    if not raw_token or len(raw_token) > 256:
        return None
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    return get_auth_store().get_user_for_session(token_hash)


def require_user(request: Request) -> dict:
    user = _current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Sign in with an approved account.")
    return user


def require_roles(*allowed_roles: str):
    def dependency(user: Annotated[dict, Depends(require_user)]) -> dict:
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Your account role cannot perform this action.",
            )
        return user

    return dependency


def require_admin_bridge(request: Request) -> dict:
    authorization = request.headers.get("authorization", "")
    scheme, separator, raw_token = authorization.partition(" ")
    if (
        not separator
        or scheme.lower() != "bearer"
        or not raw_token
        or len(raw_token) > 256
        or raw_token.strip() != raw_token
    ):
        raise HTTPException(status_code=401, detail="A read-only Admin bridge token is required.")
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    store = get_auth_store()
    principal = store.get_admin_bridge_principal(token_hash)
    if principal is None:
        raise HTTPException(status_code=401, detail="The Admin bridge token is invalid or expired.")
    if not store.consume_api_key_request(
        principal["api_key_id"],
        maximum=30,
        window_seconds=60,
    ):
        raise HTTPException(status_code=429, detail="Admin bridge request limit exceeded.")
    return principal


def _csrf_valid(request: Request) -> bool:
    cookie_token = request.cookies.get(_CSRF_COOKIE, "")
    header_token = request.headers.get("x-csrf-token", "")
    if not cookie_token or not header_token:
        return False
    if len(cookie_token) > 128 or len(header_token) > 128:
        return False
    if not secrets.compare_digest(cookie_token, header_token):
        return False
    origin = request.headers.get("origin")
    if origin:
        parsed = urlsplit(origin)
        request_host = request.headers.get("host", "").lower()
        if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != request_host:
            return False
    return True


class RequestBodyLimitMiddleware:
    """Enforce request size on the ASGI receive stream without consuming it early."""

    def __init__(self, app, *, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send) -> None:
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        headers = {name.lower(): value for name, value in scope.get("headers", ())}
        content_length = headers.get(b"content-length")
        if content_length is not None:
            try:
                raw_length = content_length.decode("ascii")
                if not raw_length.isdecimal():
                    raise ValueError
                if int(raw_length) > self.max_bytes:
                    await Response("Request body too large.", status_code=413)(scope, receive, send)
                    return
            except (UnicodeDecodeError, ValueError):
                await Response("Invalid content length.", status_code=400)(scope, receive, send)
                return

        received_bytes = 0
        request_too_large = False
        response_body_sent = False
        error_body = b"Request body too large."

        async def limited_receive():
            nonlocal received_bytes, request_too_large
            message = await receive()
            if message.get("type") == "http.request":
                received_bytes += len(message.get("body", b""))
                if received_bytes > self.max_bytes:
                    request_too_large = True
                    return {"type": "http.request", "body": b"", "more_body": False}
            return message

        async def limited_send(message):
            nonlocal response_body_sent
            if request_too_large and message.get("type") == "http.response.start":
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() not in {b"content-type", b"content-length"}
                ]
                headers.extend(
                    [
                        (b"content-type", b"text/plain; charset=utf-8"),
                        (b"content-length", str(len(error_body)).encode()),
                    ]
                )
                message = {**message, "status": 413, "headers": headers}
            elif request_too_large and message.get("type") == "http.response.body":
                if response_body_sent:
                    return
                response_body_sent = True
                message = {**message, "body": error_body, "more_body": False}
            await send(message)

        await self.app(scope, limited_receive, limited_send)


@app.middleware("http")
async def secure_request_middleware(request: Request, call_next):
    rejection: Response | None = None

    bearer_api_request = request.url.path == "/api/v1/assistant/chat" and request.headers.get(
        "authorization", ""
    ).lower().startswith("bearer ")
    if (
        rejection is None
        and request.method not in _SAFE_METHODS
        and not bearer_api_request
        and not _csrf_valid(request)
    ):
        rejection = Response(
            '{"detail":"CSRF validation failed. Refresh the page and try again."}',
            status_code=403,
            media_type="application/json",
        )

    response = rejection if rejection is not None else await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' https://accounts.google.com/gsi/client; "
        "style-src 'self'; img-src 'self' data:; font-src 'self'; "
        "connect-src 'self' https://accounts.google.com/gsi/; "
        "frame-src https://accounts.google.com/gsi/; object-src 'none'; "
        "base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
    )
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if request.url.path == "/" or request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


# Register after BaseHTTPMiddleware so the ASGI receive wrapper is outermost.
app.add_middleware(RequestBodyLimitMiddleware, max_bytes=_MAX_REQUEST_BYTES)


@app.get("/", include_in_schema=False)
async def web_platform() -> FileResponse:
    return FileResponse(_WEB_DIR / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "nanou-cyber-defense-ai"}


@app.get("/ready")
async def readiness() -> dict:
    try:
        database = get_database_instance()
        with database.engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        return {"status": "ready", "database": database.mode}
    except (RuntimeError, ValueError, OSError, SQLAlchemyError):
        raise HTTPException(
            status_code=503,
            detail="Durable database is not configured or unavailable.",
        ) from None


def _verify_google_identity(credential: str) -> dict[str, str]:
    """Verify a Google Identity Services ID token using Google's trusted keys."""
    client_id = settings.google_client_id
    if not client_id:
        raise HTTPException(status_code=503, detail="Google Sign-In is not configured.")
    try:
        from google.auth.transport.requests import Request as GoogleRequest
        from google.oauth2 import id_token
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Google Sign-In verification support is unavailable.",
        ) from exc

    try:
        claims = id_token.verify_oauth2_token(credential, GoogleRequest(), client_id)
    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail="Google credential is invalid or expired.",
        ) from exc

    issuer = claims.get("iss")
    subject = claims.get("sub")
    email = claims.get("email")
    if (
        issuer not in {"accounts.google.com", "https://accounts.google.com"}
        or not isinstance(subject, str)
        or not 1 <= len(subject) <= 255
        or not isinstance(email, str)
        or len(email) > 320
        or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email)
        or claims.get("email_verified") is not True
    ):
        raise HTTPException(status_code=401, detail="Google account identity is not verified.")

    display_name = claims.get("name")
    if not isinstance(display_name, str) or not display_name.strip():
        display_name = email.split("@", 1)[0]
    display_name = " ".join(display_name.split())[:100]
    if len(display_name) < 2:
        display_name = "Google User"
    return {"subject": subject, "email": email.strip().lower(), "display_name": display_name}


@app.get("/api/auth/providers")
async def auth_providers() -> dict:
    return {
        "google": {
            "enabled": bool(settings.google_client_id),
            "client_id": settings.google_client_id if settings.google_client_id else None,
        }
    }


@app.post("/api/auth/google", response_model=None)
async def google_sign_in(
    item: GoogleSignInIn,
    request: Request,
    response: Response,
) -> dict | JSONResponse:
    identity = _verify_google_identity(item.credential)
    store = get_auth_store()
    if store.bootstrap_available():
        raise HTTPException(
            status_code=409,
            detail="The initial administrator must be created before Google registration.",
        )
    _check_rate_limit(store, request, identity["email"], "auth.google")
    user = store.get_user_by_email(identity["email"])

    if user is None:
        try:
            pending_user = store.register(
                email=identity["email"],
                display_name=identity["display_name"],
                password_hash=hash_password(secrets.token_urlsafe(48)),
                request_id=_request_id(request),
                ip_digest=_ip_digest(request),
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return JSONResponse(
            status_code=202,
            content={
                "authenticated": False,
                "pending_approval": True,
                "user": pending_user,
                "message": (
                    "Google account received. An administrator must approve this Viewer account."
                ),
            },
        )

    if not user["is_approved"] or not user["is_active"]:
        store.record_event(
            actor_user_id=user["id"],
            action="auth.google_login",
            target_type="user",
            target_id=user["id"],
            outcome="pending_or_disabled",
            request_id=_request_id(request),
            ip_digest=_ip_digest(request),
        )
        raise HTTPException(status_code=403, detail="This account is pending approval or disabled.")

    _session_token(request, response, store, user["id"])
    store.record_event(
        actor_user_id=user["id"],
        action="auth.google_login",
        target_type="user",
        target_id=user["id"],
        outcome="success",
        request_id=_request_id(request),
        ip_digest=_ip_digest(request),
    )
    public_user = {key: value for key, value in user.items() if key != "password_hash"}
    return {"authenticated": True, "user": public_user}


@app.get("/api/auth/csrf")
async def get_csrf_token(request: Request, response: Response) -> dict[str, str]:
    token = secrets.token_urlsafe(32)
    response.set_cookie(
        key=_CSRF_COOKIE,
        value=token,
        max_age=7200,
        path="/",
        secure=request.url.scheme == "https",
        httponly=False,
        samesite="strict",
    )
    return {"csrf_token": token}


@app.get("/api/auth/me")
async def auth_me(request: Request) -> dict:
    store = get_auth_store()
    user = _current_user(request)
    return {
        "authenticated": user is not None,
        "user": user,
        "bootstrap_required": store.bootstrap_available(),
    }


@app.post("/api/auth/bootstrap")
async def bootstrap_admin(
    item: AuthBootstrapIn,
    request: Request,
    response: Response,
) -> dict:
    store = get_auth_store()
    _check_rate_limit(store, request, item.email, "auth.bootstrap")
    expected_bootstrap_token = (
        settings.bootstrap_token.get_secret_value() if settings.bootstrap_token is not None else ""
    )
    if not expected_bootstrap_token or not secrets.compare_digest(
        item.bootstrap_token, expected_bootstrap_token
    ):
        store.record_event(
            actor_user_id=None,
            action="auth.bootstrap",
            target_type="platform",
            outcome="invalid_bootstrap_token",
            request_id=_request_id(request),
            ip_digest=_ip_digest(request),
        )
        raise HTTPException(
            status_code=403,
            detail="Administrator bootstrap is unavailable or unauthorized.",
        )
    if not store.bootstrap_available():
        raise HTTPException(
            status_code=409,
            detail="Initial administrator setup is already complete.",
        )
    password_hash = hash_password(item.password)
    user = store.create_bootstrap_admin(
        email=item.email,
        display_name=item.display_name,
        password_hash=password_hash,
        request_id=_request_id(request),
        ip_digest=_ip_digest(request),
    )
    if user is None:
        raise HTTPException(
            status_code=409,
            detail="Initial administrator setup is already complete.",
        )
    _session_token(request, response, store, user["id"])
    return {"user": user, "message": "Administrator account created."}


@app.post("/api/auth/register", status_code=202)
async def register_account(item: AuthRegisterIn, request: Request) -> dict:
    store = get_auth_store()
    if store.bootstrap_available():
        raise HTTPException(
            status_code=409,
            detail="The initial administrator must be created first.",
        )
    _check_rate_limit(store, request, item.email, "auth.register")
    password_hash = hash_password(item.password)
    try:
        user = store.register(
            email=item.email,
            display_name=item.display_name,
            password_hash=password_hash,
            request_id=_request_id(request),
            ip_digest=_ip_digest(request),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "user": user,
        "message": "Registration received. An administrator must approve this account.",
    }


@app.post("/api/auth/login")
async def login_account(item: AuthLoginIn, request: Request, response: Response) -> dict:
    store = get_auth_store()
    _check_rate_limit(store, request, item.email, "auth.login")
    user = store.get_user_by_email(item.email)
    password_matches = verify_password(
        item.password,
        user["password_hash"] if user else None,
    )
    if not user or not password_matches:
        store.record_event(
            actor_user_id=None,
            action="auth.login",
            target_type="user",
            outcome="failed",
            request_id=_request_id(request),
            ip_digest=_ip_digest(request),
        )
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")
    if not user["is_approved"] or not user["is_active"]:
        store.record_event(
            actor_user_id=user["id"],
            action="auth.login",
            target_type="user",
            target_id=user["id"],
            outcome="pending_or_disabled",
            request_id=_request_id(request),
            ip_digest=_ip_digest(request),
        )
        raise HTTPException(status_code=403, detail="This account is pending approval or disabled.")
    _session_token(request, response, store, user["id"])
    store.record_event(
        actor_user_id=user["id"],
        action="auth.login",
        target_type="user",
        target_id=user["id"],
        outcome="success",
        request_id=_request_id(request),
        ip_digest=_ip_digest(request),
    )
    return {"user": {key: value for key, value in user.items() if key != "password_hash"}}


@app.post("/api/auth/password")
async def change_account_password(
    item: AuthPasswordChangeIn,
    request: Request,
    response: Response,
    user: Annotated[dict, Depends(require_user)],
) -> dict[str, bool]:
    store = get_auth_store()
    _check_rate_limit(store, request, user["email"], "auth.password_change")
    account = store.get_user_by_email(user["email"])
    if account is None or not verify_password(item.current_password, account["password_hash"]):
        store.record_event(
            actor_user_id=user["id"],
            action="auth.password.change",
            target_type="user",
            target_id=user["id"],
            outcome="failed",
            request_id=_request_id(request),
            ip_digest=_ip_digest(request),
        )
        raise HTTPException(status_code=403, detail="Current password is incorrect.")
    password_hash = hash_password(item.new_password)
    changed = store.change_password(
        user_id=user["id"],
        password_hash=password_hash,
        request_id=_request_id(request),
        ip_digest=_ip_digest(request),
    )
    if not changed:
        raise HTTPException(status_code=401, detail="Sign in again before changing your password.")
    # Reissue one fresh session for this browser; every previously issued session is revoked.
    _session_token(request, response, store, user["id"])
    return {"password_changed": True}


@app.post("/api/auth/logout")
async def logout_account(request: Request, response: Response) -> dict[str, bool]:
    raw_token = request.cookies.get(settings.session_cookie_name)
    user = _current_user(request)
    if raw_token:
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        get_auth_store().revoke_session(token_hash)
    if user:
        get_auth_store().record_event(
            actor_user_id=user["id"],
            action="auth.logout",
            target_type="user",
            target_id=user["id"],
            request_id=_request_id(request),
            ip_digest=_ip_digest(request),
        )
    _clear_session_cookie(request, response)
    return {"logged_out": True}


@app.post("/api/auth/pairing")
async def create_admin_pairing(
    request: Request,
    user: Annotated[dict, Depends(require_roles("admin"))],
) -> dict:
    store = get_auth_store()
    _check_rate_limit(store, request, user["email"], "auth.admin_pairing.create")
    raw_code = f"ncd_pair_{secrets.token_urlsafe(32)}"
    try:
        pairing = store.create_admin_pairing(
            owner_user_id=user["id"],
            token_prefix=raw_code[:20],
            token_hash=hashlib.sha256(raw_code.encode("utf-8")).hexdigest(),
            request_id=_request_id(request),
            ip_digest=_ip_digest(request),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "pairing_code": raw_code,
        "expires_at": pairing["expires_at"].isoformat(),
        "expires_in_seconds": ADMIN_PAIRING_TTL_SECONDS,
        "scope": "admin:bridge:read",
        "shown_once": True,
    }


@app.post("/api/auth/pairing/exchange")
async def exchange_admin_pairing(
    item: AdminPairingExchangeIn,
    request: Request,
) -> dict:
    store = get_auth_store()
    pairing_fingerprint = hashlib.sha256(item.pairing_code.encode("utf-8")).hexdigest()
    _check_rate_limit(store, request, pairing_fingerprint, "auth.admin_pairing.exchange")
    raw_bridge_token = f"ncd_bridge_{secrets.token_urlsafe(32)}"
    bridge = store.exchange_admin_pairing(
        pairing_token_hash=hashlib.sha256(item.pairing_code.encode("utf-8")).hexdigest(),
        bridge_token_prefix=raw_bridge_token[:20],
        bridge_token_hash=hashlib.sha256(raw_bridge_token.encode("utf-8")).hexdigest(),
        request_id=_request_id(request),
        ip_digest=_ip_digest(request),
    )
    if bridge is None:
        raise HTTPException(
            status_code=401,
            detail="The pairing code is invalid, expired, or already used.",
        )
    return {
        "bridge_token": raw_bridge_token,
        "user": bridge["user"],
        "expires_at": bridge["expires_at"].isoformat(),
        "expires_in_seconds": ADMIN_BRIDGE_TTL_SECONDS,
        "scope": "admin:bridge:read",
    }


@app.get("/api/admin/bridge/me")
async def admin_bridge_me(
    user: Annotated[dict, Depends(require_admin_bridge)],
) -> dict:
    return {
        key: user[key]
        for key in ("id", "email", "display_name", "role", "is_approved", "is_active")
    }


@app.get("/api/admin/bridge/users")
async def admin_bridge_users(
    user: Annotated[dict, Depends(require_admin_bridge)],
) -> list[dict]:
    return get_auth_store().list_users()


@app.get("/api/admin/bridge/audit")
async def admin_bridge_audit(
    user: Annotated[dict, Depends(require_admin_bridge)],
    limit: int = Query(default=100, ge=1, le=100),
) -> list[dict]:
    return get_auth_store().list_audit_events(limit)


@app.post("/api/admin/bridge/revoke")
async def revoke_admin_bridge(
    request: Request,
    user: Annotated[dict, Depends(require_admin_bridge)],
) -> dict[str, bool]:
    authorization = request.headers.get("authorization", "")
    _, _, raw_token = authorization.partition(" ")
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    revoked = get_auth_store().revoke_admin_bridge(
        token_hash,
        request_id=_request_id(request),
        ip_digest=_ip_digest(request),
    )
    return {"revoked": revoked}


@app.get("/api/admin/users")
async def admin_list_users(
    user: Annotated[dict, Depends(require_roles("admin"))],
) -> list[dict]:
    return get_auth_store().list_users()


@app.patch("/api/admin/users/{user_id}")
async def admin_update_user(
    user_id: str,
    item: AdminUserUpdateIn,
    request: Request,
    user: Annotated[dict, Depends(require_roles("admin"))],
) -> dict:
    try:
        updated = get_auth_store().update_user(
            actor_user_id=user["id"],
            target_user_id=user_id,
            role=item.role,
            is_active=item.is_active,
            request_id=_request_id(request),
            ip_digest=_ip_digest(request),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return updated


@app.get("/api/admin/audit")
async def admin_audit_events(
    user: Annotated[dict, Depends(require_roles("admin"))],
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict]:
    return get_auth_store().list_audit_events(limit)


@app.get("/api/developer/keys")
async def list_developer_api_keys(
    user: Annotated[dict, Depends(require_roles("admin", "analyst"))],
) -> list[dict]:
    return get_auth_store().list_api_keys(user["id"])


@app.post("/api/developer/keys")
async def create_developer_api_key(
    item: DeveloperApiKeyCreateIn,
    request: Request,
    user: Annotated[dict, Depends(require_roles("admin", "analyst"))],
) -> dict:
    raw_token = f"ncd_live_{secrets.token_urlsafe(32)}"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    try:
        key = get_auth_store().create_api_key(
            owner_user_id=user["id"],
            name=item.name,
            token_prefix=raw_token[:20],
            token_hash=token_hash,
            scopes=item.scopes,
            expires_at=datetime.now(UTC) + timedelta(days=item.expires_in_days),
            request_id=_request_id(request),
            ip_digest=_ip_digest(request),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "key": key,
        "token": raw_token,
        "shown_once": True,
        "warning": "Copy this token now. It cannot be retrieved again.",
    }


@app.delete("/api/developer/keys/{key_id}")
async def revoke_developer_api_key(
    key_id: str,
    request: Request,
    user: Annotated[dict, Depends(require_roles("admin", "analyst"))],
) -> dict:
    key = get_auth_store().revoke_api_key(
        owner_user_id=user["id"],
        key_id=key_id,
        request_id=_request_id(request),
        ip_digest=_ip_digest(request),
    )
    if key is None:
        raise HTTPException(status_code=404, detail="API key not found.")
    return {"revoked": True, "key": key}


async def _assistant_command_response(
    item: AssistantChatIn,
    request: Request,
    user: dict,
    scopes: set[str],
) -> dict:
    store = get_auth_store()
    fingerprint = hashlib.sha256(f"assistant:{user['id']}".encode()).hexdigest()
    if not store.allow_attempt(
        fingerprint,
        maximum=settings.assistant_requests_per_minute,
        window_seconds=60,
    ):
        store.record_event(
            actor_user_id=user["id"],
            action="assistant.rate_limited",
            target_type="assistant",
            outcome="blocked",
            request_id=_request_id(request),
            ip_digest=_ip_digest(request),
        )
        raise HTTPException(status_code=429, detail="Assistant request limit exceeded.")

    history = [turn.model_dump() for turn in item.history]
    try:
        result = await run_assistant(
            item.message,
            history,
            role=user["role"],
            scopes=scopes,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (RuntimeError, httpx.HTTPError, SQLAlchemyError) as exc:
        raise HTTPException(
            status_code=502,
            detail="The assistant could not complete that defensive lookup.",
        ) from exc

    store.record_event(
        actor_user_id=user["id"],
        action="assistant.command",
        target_type="assistant",
        target_id=str(result.get("action", "chat"))[:100],
        outcome="success" if result.get("executed") else "pending",
        request_id=_request_id(request),
        ip_digest=_ip_digest(request),
    )
    return {
        **result,
        "role": user["role"],
        "request_id": _request_id(request),
    }


@app.post("/api/chat/command")
async def assistant_chat_command(
    item: AssistantChatIn,
    request: Request,
    user: Annotated[dict, Depends(require_user)],
) -> dict:
    # Session users may read the same information available to their RBAC role.
    scopes = {"intel:read", "malware:metadata:read"}
    return await _assistant_command_response(item, request, user, scopes)


def require_api_scope(required_scope: str):
    def dependency(request: Request) -> dict:
        authorization = request.headers.get("authorization", "")
        scheme, separator, raw_token = authorization.partition(" ")
        if (
            scheme.lower() != "bearer"
            or not separator
            or not raw_token.startswith("ncd_live_")
            or len(raw_token) > 128
        ):
            raise HTTPException(
                status_code=401,
                detail="A valid Nanou Developer API Bearer token is required.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        store = get_auth_store()
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        principal = store.get_api_key_principal(token_hash)
        if principal is None:
            raise HTTPException(
                status_code=401,
                detail="API token is invalid, expired, revoked, or its owner is inactive.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if required_scope not in principal["api_key_scopes"]:
            raise HTTPException(status_code=403, detail="API token lacks the required scope.")
        if not store.consume_api_key_request(
            principal["api_key_id"],
            maximum=settings.api_key_requests_per_minute,
            window_seconds=60,
        ):
            raise HTTPException(status_code=429, detail="API key request limit exceeded.")
        return principal

    return dependency


@app.get("/api/mcp/tools")
async def mcp_tools() -> list[dict[str, str]]:
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "access": tool.access,
            "required_scope": tool.required_scope,
        }
        for tool in list_tools()
    ]


@app.get("/api/kev")
async def kev_catalog() -> dict:
    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
            return await fetch_kev_catalog(client)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="CISA KEV feed unavailable or invalid") from exc


@app.get("/api/cve/{cve_id}")
async def cve_detail(cve_id: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
            return await fetch_cve(cve_id, client)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid CVE identifier") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="NVD API unavailable") from exc


@app.get("/api/v1/kev")
async def api_v1_kev_catalog(
    _principal: Annotated[dict, Depends(require_api_scope("intel:read"))],
) -> dict:
    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
            return await fetch_kev_catalog(client)
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="CISA KEV feed unavailable or invalid") from exc


@app.get("/api/v1/cve/{cve_id}")
async def api_v1_cve_detail(
    cve_id: str,
    _principal: Annotated[dict, Depends(require_api_scope("intel:read"))],
) -> dict:
    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
            return await fetch_cve(cve_id, client)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid CVE identifier") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="NVD API unavailable") from exc


@app.get("/api/v1/malware/metadata", response_model=list[MalwareMetadata])
async def api_v1_malware_metadata(
    _principal: Annotated[dict, Depends(require_api_scope("malware:metadata:read"))],
    limit: int = Query(default=100, ge=1, le=100),
) -> list[MalwareMetadata]:
    return get_store().list(limit)


@app.post("/api/v1/assistant/chat")
async def api_v1_assistant_chat(
    item: AssistantChatIn,
    request: Request,
    principal: Annotated[dict, Depends(require_api_scope("ai:chat"))],
) -> dict:
    return await _assistant_command_response(
        item,
        request,
        principal,
        set(principal["api_key_scopes"]),
    )


@app.get("/api/attack/scopes")
async def list_attack_scopes(
    user: Annotated[dict, Depends(require_roles("admin", "analyst"))],
) -> list[dict]:
    return get_attack_store().list_scopes(include_inactive=user["role"] == "admin")


@app.post("/api/attack/scopes", status_code=201)
async def create_attack_scope(
    item: AttackScopeCreateIn,
    request: Request,
    user: Annotated[dict, Depends(require_roles("admin"))],
) -> dict:
    auth_store = get_auth_store()
    fingerprint = hashlib.sha256(f"attack.scope:{user['id']}".encode()).hexdigest()
    if not auth_store.allow_attempt(
        fingerprint,
        maximum=settings.attack_scope_creations_per_day,
        window_seconds=86400,
    ):
        auth_store.record_event(
            actor_user_id=user["id"],
            action="attack.scope.create.rate_limited",
            target_type="attack_scope",
            outcome="blocked",
            request_id=_request_id(request),
            ip_digest=_ip_digest(request),
        )
        raise HTTPException(status_code=429, detail="Attack scope creation limit exceeded.")
    expires_at = datetime.combine(item.authorization_expires_on, datetime.max.time()).replace(
        tzinfo=UTC
    )
    scope = get_attack_store().create_scope(
        created_by_user_id=user["id"],
        name=item.name,
        target=item.target,
        authorization_basis=item.authorization_basis,
        authorization_expires_at=expires_at,
    )
    auth_store.record_event(
        actor_user_id=user["id"],
        action="attack.scope.create",
        target_type="attack_scope",
        target_id=scope["id"],
        outcome="success",
        request_id=_request_id(request),
        ip_digest=_ip_digest(request),
    )
    return scope


@app.post("/api/attack/scopes/{scope_id}/revoke")
async def revoke_attack_scope(
    scope_id: str,
    request: Request,
    user: Annotated[dict, Depends(require_roles("admin"))],
) -> dict:
    store = get_attack_store()
    scope = store.get_scope(scope_id)
    if scope is None:
        raise HTTPException(status_code=404, detail="Attack scope not found.")
    if scope["is_active"]:
        scope = store.deactivate_scope(scope_id)
    get_auth_store().record_event(
        actor_user_id=user["id"],
        action="attack.scope.revoke",
        target_type="attack_scope",
        target_id=scope_id,
        outcome="success",
        request_id=_request_id(request),
        ip_digest=_ip_digest(request),
    )
    return {"revoked": True, "scope": scope}


@app.post("/api/attack/simulations", status_code=201)
async def create_attack_simulation(
    item: AttackSimulationCreateIn,
    request: Request,
    user: Annotated[dict, Depends(require_roles("admin", "analyst"))],
) -> dict:
    auth_store = get_auth_store()
    fingerprint = hashlib.sha256(f"attack.simulation:{user['id']}".encode()).hexdigest()
    if not auth_store.allow_attempt(
        fingerprint,
        maximum=settings.attack_simulations_per_hour,
        window_seconds=3600,
    ):
        auth_store.record_event(
            actor_user_id=user["id"],
            action="attack.simulation.rate_limited",
            target_type="attack_simulation",
            outcome="blocked",
            request_id=_request_id(request),
            ip_digest=_ip_digest(request),
        )
        raise HTTPException(status_code=429, detail="Attack simulation limit exceeded.")
    try:
        report = get_attack_store().create_simulation(
            actor_user_id=user["id"],
            scope_id=item.scope_id,
            profile=item.profile,
            intensity=item.intensity,
            duration_minutes=item.duration_minutes,
        )
    except LookupError as exc:
        auth_store.record_event(
            actor_user_id=user["id"],
            action="attack.simulation.scope_missing",
            target_type="attack_scope",
            target_id=item.scope_id,
            outcome="blocked",
            request_id=_request_id(request),
            ip_digest=_ip_digest(request),
        )
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        auth_store.record_event(
            actor_user_id=user["id"],
            action="attack.simulation.scope_blocked",
            target_type="attack_scope",
            target_id=item.scope_id,
            outcome="blocked",
            request_id=_request_id(request),
            ip_digest=_ip_digest(request),
        )
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    auth_store.record_event(
        actor_user_id=user["id"],
        action="attack.simulation.create",
        target_type="attack_simulation",
        target_id=report["id"],
        outcome="success",
        request_id=_request_id(request),
        ip_digest=_ip_digest(request),
    )
    return report


@app.get("/api/attack/simulations")
async def list_attack_simulations(
    _user: Annotated[dict, Depends(require_roles("admin", "analyst"))],
    limit: int = Query(default=30, ge=1, le=100),
) -> list[dict]:
    return get_attack_store().list_simulations(limit)


@app.get("/api/attack/simulations/{simulation_id}")
async def get_attack_simulation(
    simulation_id: str,
    _user: Annotated[dict, Depends(require_roles("admin", "analyst"))],
) -> dict:
    report = get_attack_store().get_simulation(simulation_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Attack simulation not found.")
    return report


@app.get("/api/v1/openapi.json")
async def api_v1_openapi(request: Request) -> dict:
    bearer_security = {"NanouBearer": []}
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Nanou Cyber Defense API",
            "version": "1.0.0",
            "description": (
                "Read-only API for authorized threat-intelligence and malware-metadata "
                "integrations. Use an expiring Developer API key in the HTTP Authorization "
                "Bearer header. No administrative, write, binary-upload or inference endpoints "
                "are exposed by this external API. The optional assistant chat uses a "
                "strict defensive read-only tool allowlist."
            ),
        },
        "servers": [{"url": str(request.base_url).rstrip("/")}],
        "components": {
            "securitySchemes": {
                "NanouBearer": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "ncd_live_…",
                    "description": (
                        "Create a scoped key in Developer Center. Never put it in a URL."
                    ),
                }
            },
            "schemas": {
                "CveRecord": {"type": "object", "additionalProperties": True},
                "KevCatalog": {"type": "object", "additionalProperties": True},
                "MalwareMetadata": {"type": "object", "additionalProperties": True},
                "AssistantChatTurn": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "enum": ["user", "assistant"]},
                        "content": {"type": "string", "minLength": 1, "maxLength": 1200},
                    },
                    "required": ["role", "content"],
                    "additionalProperties": False,
                },
                "AssistantChatRequest": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "minLength": 1, "maxLength": 1000},
                        "history": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/AssistantChatTurn"},
                            "maxItems": 8,
                        },
                    },
                    "required": ["message"],
                    "additionalProperties": False,
                },
                "AssistantChatResponse": {
                    "type": "object",
                    "properties": {
                        "reply": {"type": "string"},
                        "action": {"type": "string"},
                        "executed": {"type": "boolean"},
                        "mode": {"type": "string"},
                        "role": {"type": "string"},
                        "request_id": {"type": "string"},
                    },
                    "required": ["reply", "action", "executed", "mode", "role", "request_id"],
                    "additionalProperties": True,
                },
            },
        },
        "paths": {
            "/api/v1/kev": {
                "get": {
                    "operationId": "listCisaKev",
                    "summary": "Read the CISA Known Exploited Vulnerabilities catalog",
                    "security": [bearer_security],
                    "responses": {
                        "200": {
                            "description": "Current CISA KEV catalog",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/KevCatalog"}
                                }
                            },
                        }
                    },
                }
            },
            "/api/v1/cve/{cve_id}": {
                "get": {
                    "operationId": "getNvdCve",
                    "summary": "Read one CVE record from NVD",
                    "security": [bearer_security],
                    "parameters": [
                        {
                            "name": "cve_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "pattern": "^CVE-[0-9]{4}-[0-9]{4,}$"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "NVD vulnerability record",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/CveRecord"}
                                }
                            },
                        }
                    },
                }
            },
            "/api/v1/malware/metadata": {
                "get": {
                    "operationId": "listMalwareMetadata",
                    "summary": "Read stored malware hashes, labels and metadata",
                    "security": [bearer_security],
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "schema": {
                                "type": "integer",
                                "minimum": 1,
                                "maximum": 100,
                                "default": 100,
                            },
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Stored malware metadata",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/MalwareMetadata"},
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/api/v1/assistant/chat": {
                "post": {
                    "operationId": "runDefensiveAssistantCommand",
                    "summary": (
                        "Interpret a defensive command and execute only allowlisted read-only tools"
                    ),
                    "description": (
                        "Requires a Developer API key with ai:chat and the additional read scope "
                        "for each requested data source. Does not expose shell or write actions."
                    ),
                    "security": [bearer_security],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/AssistantChatRequest"}
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Assistant reply and read-only tool results",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/AssistantChatResponse"}
                                }
                            },
                        },
                        "401": {"description": "Missing, expired or revoked Developer API key"},
                        "403": {"description": "The API key lacks the assistant or data scope"},
                        "429": {"description": "Assistant or API key rate limit exceeded"},
                    },
                }
            },
        },
    }


def load_configured_malware_model():
    if (
        settings.malware_model_path is None
        or settings.malware_model_sha256 is None
        or settings.malware_model_dataset_id is None
    ):
        raise ValueError("No malware model has been configured.")
    return load_verified_model(
        str(settings.malware_model_path),
        settings.malware_model_sha256,
        settings.malware_model_dataset_id,
    )


@app.get("/api/malware/inference/status")
async def malware_inference_status() -> dict:
    if (
        settings.malware_model_path is None
        or settings.malware_model_sha256 is None
        or settings.malware_model_dataset_id is None
    ):
        return {"available": False, "reason": "No verified malware model is configured."}
    try:
        model = load_configured_malware_model()
    except (OSError, RuntimeError, ValueError):
        return {
            "available": False,
            "reason": "The configured malware model failed integrity or schema verification.",
        }
    return {
        "available": True,
        "dataset_id": model.dataset_id,
        "feature_count": len(model.feature_names),
        "schema_version": 1,
        "decision_threshold": settings.malware_model_threshold,
    }


@app.post("/api/malware/features/prepare/{dataset_id}")
async def prepare_features(
    dataset_id: str,
    request: Request,
    user: Annotated[dict, Depends(require_roles("admin", "analyst"))],
) -> dict:
    if dataset_id not in {"ember2024-apk", "lamda-apk-2022-train-2023-test"}:
        raise HTTPException(status_code=422, detail="Unsupported feature dataset.")
    content_type = request.headers.get("content-type", "").split(";", maxsplit=1)[0].strip().lower()
    if content_type not in {"text/csv", "text/plain"}:
        raise HTTPException(status_code=415, detail="Submit pre-extracted CSV text only.")
    raw_content = bytearray()
    async for chunk in request.stream():
        if len(raw_content) + len(chunk) > 1_048_576:
            raise HTTPException(
                status_code=413,
                detail="Feature CSV exceeds the 1 MiB upload limit.",
            )
        raw_content.extend(chunk)
    try:
        content = bytes(raw_content).decode("utf-8")
        prepared = prepare_feature_csv(content, dataset_id)
    except (UnicodeDecodeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    get_auth_store().record_event(
        actor_user_id=user["id"],
        action="malware.features.prepare",
        target_type="feature-dataset",
        target_id=dataset_id,
        request_id=_request_id(request),
        ip_digest=_ip_digest(request),
    )
    return prepared


@app.post(
    "/api/malware/inference",
    response_model=MalwareInferenceResult,
)
async def malware_inference(
    item: MalwareInferenceIn,
    user: Annotated[dict, Depends(require_roles("admin", "analyst"))],
    request: Request,
) -> MalwareInferenceResult:
    try:
        model = load_configured_malware_model()
    except (OSError, RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail="No verified malware model is available for inference.",
        ) from exc
    if item.dataset_id != model.dataset_id:
        raise HTTPException(
            status_code=422,
            detail="The requested feature dataset does not match the configured model.",
        )
    try:
        result = classify_features(
            model,
            item.features,
            threshold=settings.malware_model_threshold,
        )
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail="Malware model inference failed.") from exc
    get_auth_store().record_event(
        actor_user_id=user["id"],
        action="malware.inference",
        target_type="feature-dataset",
        target_id=item.dataset_id,
        request_id=_request_id(request),
        ip_digest=_ip_digest(request),
    )
    return MalwareInferenceResult.model_validate(result)


@app.get("/api/malware/metadata", response_model=list[MalwareMetadata])
async def list_malware_metadata(
    user: Annotated[dict, Depends(require_user)],
    limit: int = Query(default=100, ge=1, le=500),
):
    return get_store().list(limit)


@app.post("/api/malware/metadata", response_model=MalwareMetadata, status_code=201)
async def add_malware_metadata(
    item: MalwareMetadataIn,
    user: Annotated[dict, Depends(require_roles("admin", "analyst"))],
    request: Request,
) -> MalwareMetadata:
    record = get_store().add(item)
    get_auth_store().record_event(
        actor_user_id=user["id"],
        action="malware.metadata.create",
        target_type="malware-metadata",
        target_id=record.sha256,
        request_id=_request_id(request),
        ip_digest=_ip_digest(request),
    )
    return record
