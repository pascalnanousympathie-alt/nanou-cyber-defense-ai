import httpx
import re

NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
_CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)


async def fetch_cve(cve_id: str, client: httpx.AsyncClient) -> dict:
    if not _CVE_RE.fullmatch(cve_id):
        raise ValueError("Invalid CVE identifier")
    response = await client.get(NVD_URL, params={"cveId": cve_id.upper()})
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Unexpected NVD response schema")
    return payload
