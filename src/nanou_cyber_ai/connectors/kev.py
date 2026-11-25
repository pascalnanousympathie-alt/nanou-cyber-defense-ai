import httpx

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"


async def fetch_kev_catalog(client: httpx.AsyncClient) -> dict:
    response = await client.get(KEV_URL)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict) or not isinstance(payload.get("vulnerabilities"), list):
        raise ValueError("Unexpected CISA KEV response schema")
    return payload
