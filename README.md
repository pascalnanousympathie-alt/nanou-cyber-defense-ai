# Nanou Cyber Defense AI

A defensive, browser-based cybersecurity platform. The first release focuses on vulnerability intelligence, malware **metadata and static-feature** analysis, and an auditable, permission-scoped MCP gateway. The primary interface is a responsive website; there is no Android APK requirement.

> **Safety boundary:** this repository does not store, build, execute, or distribute malware binaries or offensive payloads. Malware research uses hashes, labels, public intelligence, and pre-extracted feature datasets (for example EMBER 2018/2024). All agents are designed for defensive analysis and remediation.

## MVP scope

- Responsive web dashboard served by FastAPI for health, NVD CVE lookup, CISA KEV intelligence, MCP inventory and protected malware metadata.
- Modular defensive agents for research, triage, code review and remediation recommendations.
- Optional official MCP Python SDK v2 server (stdio) exposing only NVD and CISA read-only tools.
- Malware feature-data manifests, validated metadata ingestion and a baseline static-feature classifier.
- CI with lint, format and tests using standard GitHub-hosted runners.
- Authorized Red Team tabletop simulations with an Admin-managed target allowlist, operator-declared authorization basis and expiry, Analyst-run local scenario checklists, MITRE ATT&CK references, draft SOC detection recommendations, audit history, and JSON reports. No live probing or exploit execution.

## Architecture

See [docs/architecture.md](docs/architecture.md), [docs/mcp.md](docs/mcp.md), [docs/safety-design.md](docs/safety-design.md), and the [Attack Simulation Manager guide](docs/attack-simulation.md).

## Quick start

Python 3.11+ recommended.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn nanou_cyber_ai.api:app --host 127.0.0.1 --port 8000
```

Open the web dashboard at `http://127.0.0.1:8000/` after starting the service.

Health: `GET /health`

- `GET /api/mcp/tools` — list the registered, scope-limited tools.
- `GET /api/kev` — fetch the CISA Known Exploited Vulnerabilities catalog.
- `GET /api/cve/{cve_id}` — fetch one CVE from the NVD API.
- `GET /api/auth/me` — current account and first-Admin setup status.
- `POST /api/auth/bootstrap` — one-time first Administrator setup (requires a private bootstrap token).
- `POST /api/auth/register`, `/api/auth/login`, `/api/auth/logout` — account and session lifecycle.
- `GET /api/admin/users`, `PATCH /api/admin/users/{id}`, `GET /api/admin/audit` — Admin-only RBAC and audit operations.
- `GET /api/malware/metadata` — list stored metadata (authenticated account).
- `POST /api/malware/metadata` — add a hash/label/feature-summary record (Admin/Analyst only; never a binary).

- `GET /api/malware/inference/status` — report whether an operator-configured model passed integrity/schema checks.
- `POST /api/malware/features/prepare/{dataset_id}` — validate one pre-extracted feature CSV row (Admin/Analyst only).
- `POST /api/malware/inference` — classify an exact numeric feature vector (Admin/Analyst only; no APK or binary uploads).

Local development uses SQLite under `~/.local/share/nanou-cyber-defense-ai` by default. Hosted/serverless environments require a dedicated PostgreSQL `NANOU_DATABASE_URL` and a private `NANOU_BOOTSTRAP_TOKEN`. Passwords are hashed with Argon2id; browser sessions use HttpOnly cookies and CSRF protection. Never put actual secrets, private reports, customer data, or malware samples in this public repository.

## Web platform

The responsive web interface is served directly by FastAPI; it uses local CSS/JavaScript assets and does not need a separate frontend build or external CDN. See [the web platform guide](docs/web-platform.md), [Attack Simulation Manager guide](docs/attack-simulation.md), and [deployment runbook](docs/deployment.md) for authentication, tabletop scenarios, feature CSV preparation and hosting configuration.

## Optional MCP server

```bash
python -m pip install -e ".[mcp]"
python -m nanou_cyber_ai.mcp.server
```

The MCP server uses local stdio and exposes only fixed-origin NVD/CISA read-only lookups. See [docs/mcp.md](docs/mcp.md).

## EMBER2024 import and model

The official EMBER2024 project publishes pre-extracted JSONL features and a `thrember` vectorizer. The safe importer below downloads the official feature archives and extracts **flat JSONL files only**. It rejects traversal paths, symlinks, unexpected file types, oversized archives and overwrite attempts. It never extracts executable samples.

On a capable Linux workstation (the upstream feature toolkit has substantial dependencies; do not install its full stack on a low-memory Android phone):

```bash
python -m pip install -e ".[ember-download]"
mkdir -p /data/ember2024
python scripts/import_ember2024_archives.py --data-dir /data/ember2024 --subset train --file-type APK
python scripts/import_ember2024_archives.py --data-dir /data/ember2024 --subset test --file-type APK
python scripts/import_ember2024_archives.py --data-dir /data/ember2024 --subset challenge
```

Then install the upstream vectorizer and produce the numeric matrices:

```bash
python -m pip install "git+https://github.com/FutureComputing4AI/EMBER2024.git@0ef753e81d98bf209f71b03cd331dfc190b5b54d"
python -c "import thrember; thrember.create_vectorized_features('/data/ember2024')"
```

The upstream vectorizer currently expects the challenge JSONL subset as well as train/test. The challenge files are feature metadata, not executable samples. After vectorization:

```bash
python scripts/export_ember_features.py --data-dir /data/ember2024 --subset train --output datasets/cache/ember2024-apk-train.csv
python scripts/export_ember_features.py --data-dir /data/ember2024 --subset test --output datasets/cache/ember2024-apk-test.csv
python -m pip install -e ".[ml]"
python scripts/train_static_malware_detector.py \
  --train-csv datasets/cache/ember2024-apk-train.csv \
  --test-csv datasets/cache/ember2024-apk-test.csv \
  --dataset-id ember2024-apk
```

The exporter defaults to 2,000 source rows for train and 500 for test to bound disk/memory. Adjust `--max-source-rows` only when storage and memory are sufficient. The trainer uses compact float32/int8 buffers, defaults to 2,000 train rows, 500 test rows and up to 4,096 features, and keeps the upstream temporal split. See [docs/malware-model.md](docs/malware-model.md) for the full workflow and limitations.

The model and metrics are written under the ignored `models/` directory; dataset files and generated CSVs remain under ignored `datasets/cache/`. Neither is committed to Git. Verify the upstream dataset license and terms before reuse or redistribution.

## CI

GitHub Actions runs tests and static checks. Standard GitHub-hosted runner usage is free for public repositories, subject to GitHub's other concurrency, rate and platform limits. See GitHub's [Actions billing](https://docs.github.com/en/actions/concepts/billing-and-usage) and [Actions limits](https://docs.github.com/en/actions/reference/limits).

## Status

Web platform with defensive CVE/KEV intelligence, Argon2id multi-user authentication, Admin/Analyst/Viewer RBAC, CSRF protection, audit logs, PostgreSQL persistence and pre-extracted feature CSV validation. The dashboard also includes a guarded AI Chat Command Center: local read-only commands work without an LLM key; optional server-side Responses API tool selection requires `NANOU_AI_API_KEY` and is restricted to a defensive read-only allowlist. The Attack Simulation Manager creates only deterministic tabletop reports for Admin-authorized, unexpired target scopes; it performs zero network requests and executes no exploits, payloads, malware, or automated changes. No provider key is configured by default. The Vercel deployment remains protected by SSO for all deployment targets; no unprotected public launch or autonomous changes to customer systems are enabled. The optional static-feature inference endpoint remains unavailable until a trusted model artifact is configured.
