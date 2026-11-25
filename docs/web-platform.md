# Nanou Cyber Defense AI — Web platform

The application is delivered as a responsive browser-based platform served by the existing FastAPI service. It does not require an Android APK, a Node build chain, external frontend CDNs, or browser extensions.

## Current web interface

- `/` — responsive dashboard in Malagasy, suitable for phone and desktop browsers.
- `/api/cve/{cve_id}` — read-only NVD vulnerability lookup.
- `/api/kev` — read-only CISA Known Exploited Vulnerabilities feed.
- `/api/mcp/tools` — inventory of the registered, scope-limited MCP tools.
- `/api/malware/metadata` — protected local metadata listing and ingestion; requires a bearer token.
- `/docs` — FastAPI API documentation.

The dashboard uses same-origin API requests. Remote feed content is rendered as text, not interpreted as HTML. The metadata token is held in page memory only; it is not written to cookies, local storage or session storage. Reloading the page clears the token.

## Run locally

```bash
python -m pip install -e ".[dev]"
export NANOU_METADATA_API_TOKEN="<set-a-long-random-token-locally>"
uvicorn nanou_cyber_ai.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/` from the same device. Do not expose this development server directly to the public internet.

## Configure the feature classifier

Install the optional ML dependencies on the server and configure one trusted artifact produced by the controlled benchmark workflow:

~~~bash
python -m pip install -e ".[ml]"
export NANOU_MALWARE_MODEL_PATH="/absolute/path/to/static-malware-detector-v1.joblib"
export NANOU_MALWARE_MODEL_SHA256="<trusted-artifact-sha256>"
export NANOU_MALWARE_MODEL_DATASET_ID="ember2024-apk"
export NANOU_METADATA_API_TOKEN="<long-random-token>"
~~~

Use ember2024-apk only with its 2,568 named EMBER features, or lamda-apk-2022-train-2023-test only with its 4,561 signed-int8 LAMDA features. One model is configured per service process. The browser can submit a JSON array of pre-extracted numbers; it cannot upload APKs or model files. The inference endpoint checks the model file digest before deserialization, and then checks its dataset ID, schema version and exact ordered feature names. The default threshold 0.5 is experimental, not a production operating point; choose a candidate on a separate validation set and test it on a later untouched set.

## Before public deployment

This repository change supplies a web UI, not a production hosting deployment. Before opening it to public traffic, configure HTTPS and a reverse proxy, rate limits and request-size limits, individual user identity with role-based access control, audit logging, secret management and monitored backups. The current metadata endpoints use one configured bearer token; that is not a multi-user login system. Do not distribute the shared token to normal users.

The current malware workflow is feature-data-only. The site does not accept or execute APKs, PE files, scripts or other binaries. An operator may configure one trusted research model artifact with its expected SHA-256 and dataset ID. The API verifies the artifact hash, model metadata, schema version and exact feature names before using it. The inference endpoint accepts only finite numeric feature vectors; the API never deserializes an uploaded model or runs an uploaded binary.
