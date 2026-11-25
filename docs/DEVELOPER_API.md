# Developer API and AI integration

The versioned Developer API is a read-only REST interface for approved Admin and Analyst accounts, remote backend services and AI platforms that support OpenAPI 3.1 and HTTP Bearer authentication.

## Endpoints

| Method | Endpoint | Scope |
|---|---|---|
| GET | `/api/v1/kev` | `intel:read` |
| GET | `/api/v1/cve/{cve_id}` | `intel:read` |
| GET | `/api/v1/malware/metadata?limit=100` | `malware:metadata:read` |
| GET | `/api/v1/openapi.json` | Public schema |

The external API does not expose account administration, audit log, data writes, APK/binary uploads, malware inference, shell commands or autonomous remediation.

## API key lifecycle

An approved Admin or Analyst may create at most 10 active keys. A key belongs to one account, can have only `intel:read` and/or `malware:metadata:read`, expires after 1–90 days, and is shown only once. Only a SHA-256 digest and a short prefix are stored. The owner may revoke it. Keys are also revoked when their owner is disabled or their role is changed.

The default limit is 60 requests per key per minute. Configure it using `NANOU_API_KEY_REQUESTS_PER_MINUTE`.

Send the token only in an HTTPS Authorization header:

```http
Authorization: Bearer ncd_live_<one-time-token>
```

Never put it in a URL, prompt, public browser JavaScript, mobile APK, source repository or logs. Store it in a backend secret manager. API responses use `Cache-Control: no-store`.

## cURL example

```bash
export NANOU_API_BASE_URL="https://YOUR_APPROVED_API_HOST"
export NANOU_API_KEY="ncd_live_<stored-secret>"

curl --fail --silent --show-error \
  -H "Authorization: Bearer ${NANOU_API_KEY}" \
  "${NANOU_API_BASE_URL}/api/v1/kev"
```

## Python example

```python
import os
import requests

base = os.environ["NANOU_API_BASE_URL"].rstrip("/")
key = os.environ["NANOU_API_KEY"]
response = requests.get(
    f"{base}/api/v1/cve/CVE-2024-3094",
    headers={"Authorization": f"Bearer {key}"},
    timeout=20,
)
response.raise_for_status()
print(response.json())
```

## AI platform setup

1. Import the deployed `/api/v1/openapi.json` URL into an AI platform that supports OpenAPI/Actions.
2. Configure HTTP Bearer authentication.
3. Store the key in the AI platform's secret manager, not in a prompt or tool description.
4. Grant only the scope required by that AI task.
5. Test each operation and review the AI's output before acting on it.

This is a read-only data connector, not an autonomous security agent. AI summaries and triage are advisory and require analyst review.

## Deployment gate

The current Vercel deployments remain protected by Vercel Authentication for All Deployments. An external AI provider may not be able to fetch the Preview or OpenAPI schema with only a Nanou API key. Do not remove SSO just to make the integration work. Before external use, approve an HTTPS API hostname and service-to-service access model, while retaining Nanou Bearer authentication as a second layer.

Before Production data is used, isolate Preview and Production database credentials and verify backups/restores, provider identity and hosting-plan suitability. No production promotion or access-protection change is part of this work.
