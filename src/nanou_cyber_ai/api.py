import secrets
from pathlib import Path
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles

from nanou_cyber_ai.connectors.kev import fetch_kev_catalog
from nanou_cyber_ai.connectors.nvd import fetch_cve
from nanou_cyber_ai.malware.inference import classify_features, load_verified_model
from nanou_cyber_ai.mcp.registry import list_tools
from nanou_cyber_ai.models import (
    MalwareInferenceIn,
    MalwareInferenceResult,
    MalwareMetadata,
    MalwareMetadataIn,
)
from nanou_cyber_ai.settings import settings
from nanou_cyber_ai.storage.sqlite import MalwareMetadataStore

app = FastAPI(
    title="Nanou Cyber Defense AI",
    version="0.1.0",
    description="Defensive vulnerability intelligence and malware feature analysis.",
)
_bearer = HTTPBearer(auto_error=False)
_WEB_DIR = Path(__file__).resolve().parent / "web"

app.mount("/assets", StaticFiles(directory=_WEB_DIR / "assets"), name="web-assets")


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path == "/":
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
            "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
        )
        response.headers["Cache-Control"] = "no-store"
    return response


def get_store() -> MalwareMetadataStore:
    return MalwareMetadataStore(settings.data_dir)


def require_metadata_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> None:
    expected = (
        settings.metadata_api_token.get_secret_value()
        if settings.metadata_api_token is not None
        else ""
    )
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Metadata API is disabled until NANOU_METADATA_API_TOKEN is configured.",
        )
    if credentials is None or not secrets.compare_digest(credentials.credentials, expected):
        raise HTTPException(status_code=401, detail="Valid bearer token required.")


@app.get("/", include_in_schema=False)
async def web_platform() -> FileResponse:
    return FileResponse(_WEB_DIR / "index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "nanou-cyber-defense-ai"}


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


@app.post(
    "/api/malware/inference",
    response_model=MalwareInferenceResult,
    dependencies=[Depends(require_metadata_token)],
)
async def malware_inference(item: MalwareInferenceIn) -> MalwareInferenceResult:
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
    return MalwareInferenceResult.model_validate(result)


@app.get(
    "/api/malware/metadata",
    response_model=list[MalwareMetadata],
    dependencies=[Depends(require_metadata_token)],
)
async def list_malware_metadata(limit: int = Query(default=100, ge=1, le=500)):
    return get_store().list(limit)


@app.post(
    "/api/malware/metadata",
    response_model=MalwareMetadata,
    status_code=201,
    dependencies=[Depends(require_metadata_token)],
)
async def add_malware_metadata(item: MalwareMetadataIn) -> MalwareMetadata:
    return get_store().add(item)
