import secrets
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from nanou_cyber_ai.connectors.kev import fetch_kev_catalog
from nanou_cyber_ai.connectors.nvd import fetch_cve
from nanou_cyber_ai.mcp.registry import list_tools
from nanou_cyber_ai.models import MalwareMetadata, MalwareMetadataIn
from nanou_cyber_ai.settings import settings
from nanou_cyber_ai.storage.sqlite import MalwareMetadataStore

app = FastAPI(
    title="Nanou Cyber Defense AI",
    version="0.1.0",
    description="Defensive vulnerability intelligence and malware feature analysis.",
)
_bearer = HTTPBearer(auto_error=False)


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
