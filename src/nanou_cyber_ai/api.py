"""FastAPI application for the Nanou Cyber Defense web platform."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated
from urllib.parse import urlsplit

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from nanou_cyber_ai.connectors.kev import fetch_kev_catalog
from nanou_cyber_ai.connectors.nvd import fetch_cve
from nanou_cyber_ai.malware.feature_csv import prepare_feature_csv
from nanou_cyber_ai.malware.inference import classify_features, load_verified_model
from nanou_cyber_ai.mcp.registry import list_tools
from nanou_cyber_ai.models import (
    AdminUserUpdateIn,
    AuthBootstrapIn,
    AuthLoginIn,
    AuthRegisterIn,
    DeveloperApiKeyCreateIn,
    MalwareInferenceIn,
    MalwareInferenceResult,
    MalwareMetadata,
    MalwareMetadataIn,
)
from nanou_cyber_ai.security.passwords import hash_password, verify_password
from nanou_cyber_ai.settings import settings
from nanou_cyber_ai.storage.auth import AuthStore
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
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


app.mount("/assets", StaticFiles(directory=_WEB_DIR / "assets"), name="web-assets")


def get_database_instance() -> SecurityDatabase:
    database_url = (
        settings.database_url.get_secret_value() if settings.database_url is not None else None
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


def _request_id(request: Request) -> str:
    supplied = request.headers.get("x-request-id", "").strip()
    if supplied and len(supplied) <= 80 and all(ch.isalnum() or ch in "-_." for ch in supplied):
        return supplied
    return uuid.uuid4().hex


def _ip_digest(request: Request) -> str | None:
    # Use the direct peer address; do not trust arbitrary X-Forwarded-For input.
    peer = request.client.host if request.client else None
    return hashlib.sha256(peer.encode("utf-8")).hexdigest() if peer else None


def _rate_fingerprints(request: Request, email: str, action: str) -> tuple[str, str | None]:
    email_payload = f"{action}:{email}".encode()
    email_digest = hashlib.sha256(email_payload).hexdigest()
    ip_digest = _ip_digest(request)
    if ip_digest:
        ip_payload = f"{action}:{ip_digest}".encode()
        ip_digest = hashlib.sha256(ip_payload).hexdigest()
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


@app.middleware("http")
async def secure_request_middleware(request: Request, call_next):
    rejection: Response | None = None
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) < 0 or int(content_length) > _MAX_REQUEST_BYTES:
                rejection = Response("Request body too large or invalid.", status_code=413)
        except ValueError:
            rejection = Response("Invalid content length.", status_code=400)

    if rejection is None and request.method not in _SAFE_METHODS and not _csrf_valid(request):
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
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
        "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
    )
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if request.url.path == "/" or request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


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
                "are exposed by this external API."
            ),
        },
        "servers": [{"url": str(request.base_url).rstrip("/")}],
        "components": {
            "securitySchemes": {
                "NanouBearer": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "ncd_live_…",
                    "description": "Create a scoped key in Developer Center. Never put it in a URL.",
                }
            },
            "schemas": {
                "CveRecord": {"type": "object", "additionalProperties": True},
                "KevCatalog": {"type": "object", "additionalProperties": True},
                "MalwareMetadata": {"type": "object", "additionalProperties": True},
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
                            "schema": {"type": "integer", "minimum": 1, "maximum": 100, "default": 100},
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
