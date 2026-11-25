"""Local stdio MCP server exposing defensive, read-only intelligence tools.

Install the optional SDK with: pip install -e ".[mcp]"
Do not expose this server to an untrusted network.
"""
import re

import httpx
from mcp.server.mcpserver import MCPServer

from nanou_cyber_ai.connectors.kev import KEV_URL
from nanou_cyber_ai.connectors.nvd import NVD_URL
from nanou_cyber_ai.settings import settings

mcp = MCPServer("Nanou Cyber Defense AI")
_CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)


@mcp.tool()
def nvd_get_cve(cve_id: str) -> dict:
    """Look up one CVE in the official NIST NVD API."""
    if not _CVE_RE.fullmatch(cve_id):
        raise ValueError("Invalid CVE identifier")
    with httpx.Client(timeout=settings.http_timeout_seconds) as client:
        response = client.get(NVD_URL, params={"cveId": cve_id.upper()})
        response.raise_for_status()
        data = response.json()
    entries = data.get("vulnerabilities", [])
    if not entries:
        return {"cve_id": cve_id.upper(), "found": False}
    cve = entries[0].get("cve", {})
    descriptions = [
        item.get("value", "")
        for item in cve.get("descriptions", [])
        if item.get("lang") == "en"
    ]
    return {
        "cve_id": cve.get("id", cve_id.upper()),
        "found": True,
        "published": cve.get("published"),
        "last_modified": cve.get("lastModified"),
        "descriptions": descriptions[:2],
        "metrics": cve.get("metrics", {}),
    }


@mcp.tool()
def cisa_kev_check(cve_id: str) -> dict:
    """Check whether a CVE appears in the official CISA KEV catalog."""
    if not _CVE_RE.fullmatch(cve_id):
        raise ValueError("Invalid CVE identifier")
    with httpx.Client(timeout=settings.http_timeout_seconds) as client:
        response = client.get(KEV_URL)
        response.raise_for_status()
        catalog = response.json()
    match = next(
        (
            item for item in catalog.get("vulnerabilities", [])
            if item.get("cveID", "").upper() == cve_id.upper()
        ),
        None,
    )
    return {
        "cve_id": cve_id.upper(),
        "in_kev": match is not None,
        "catalog_version": catalog.get("catalogVersion"),
        "vulnerability": match,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
