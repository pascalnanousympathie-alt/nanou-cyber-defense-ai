# Nanou Cyber Defense AI

A defensive, multi-agent cybersecurity research platform. The first release focuses on vulnerability intelligence, malware **metadata and static-feature** analysis, and an auditable, permission-scoped MCP gateway.

> **Safety boundary:** this repository does not store, build, execute, or distribute malware binaries or offensive payloads. Malware research uses hashes, labels, public intelligence, and pre-extracted feature datasets (for example EMBER 2018/2024). All agents are designed for defensive analysis and remediation.

## MVP scope

- FastAPI service for health, NVD CVE lookup, CISA KEV intelligence, and malware metadata.
- Modular defensive agents for research, triage, code review and remediation recommendations.
- Optional official MCP Python SDK v2 server (stdio) exposing only NVD and CISA read-only tools.
- Malware feature-data manifests and validated metadata ingestion. Executable samples are intentionally excluded.
- CI with lint, format and tests using standard GitHub-hosted runners.

## Architecture

See [docs/architecture.md](docs/architecture.md), [docs/mcp.md](docs/mcp.md), and [docs/safety-design.md](docs/safety-design.md).

## Quick start

Python 3.11+ recommended.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn nanou_cyber_ai.api:app --host 127.0.0.1 --port 8000
```

Health: `GET /health`

- `GET /api/mcp/tools` — list the registered, scope-limited tools.
- `GET /api/kev` — fetch the CISA Known Exploited Vulnerabilities catalog.
- `GET /api/cve/{cve_id}` — fetch one CVE from the NVD API.
- `GET /api/malware/metadata` — list stored metadata records (requires bearer token).
- `POST /api/malware/metadata` — add a hash/label/feature-summary record (requires bearer token; never a binary).

The service stores metadata under `~/.local/share/nanou-cyber-defense-ai` by default. Set `NANOU_DATA_DIR` to use another directory. Set `NANOU_METADATA_API_TOKEN` locally before using metadata endpoints. Never put actual tokens, private reports, customer data, or malware samples in this public repository.

## Optional MCP server

```bash
python -m pip install -e ".[mcp]"
python -m nanou_cyber_ai.mcp.server
```

The MCP server uses local stdio and exposes only fixed-origin NVD/CISA read-only lookups. See [docs/mcp.md](docs/mcp.md).

## Malware research data

See [datasets/README.md](datasets/README.md). EMBER feature datasets contain extracted features and labels rather than executable sample files. Large datasets are not checked into Git or automatically downloaded by CI.

## CI

GitHub Actions runs tests and static checks. Standard GitHub-hosted runner usage is free for public repositories, subject to GitHub's other concurrency, rate and platform limits. See GitHub's [Actions billing](https://docs.github.com/en/actions/concepts/billing-and-usage) and [Actions limits](https://docs.github.com/en/actions/reference/limits).

## Status

MVP scaffold. External connectors require network access. No production deployment, external LLM credentials, or autonomous changes to customer systems are enabled.
