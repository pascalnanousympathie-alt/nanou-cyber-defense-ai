# Architecture

## Components

1. **API layer** — FastAPI exposes health, CVE/KEV lookups, metadata records, and the MCP tool catalog.
2. **Connectors** — fixed-origin, read-only clients for NVD and CISA KEV. No user-supplied URL is fetched.
3. **Agents** — small, composable defensive agents. The current triage agent prioritizes known-exploited CVEs and CVSS scores.
4. **Malware feature pipeline** — accepts SHA-256 identifiers, labels, provenance and numeric pre-extracted features. It does not accept or execute binaries.
5. **MCP registry** — describes available tools and checks capabilities before a caller may use a tool. No arbitrary shell or remote-control tool is registered.
6. **Storage** — SQLAlchemy-backed SQLite for local development and PostgreSQL for hosting; SQLite fallback is blocked on serverless platforms.
7. **Identity/security** — Argon2id password hashes, opaque HttpOnly sessions stored by hash, CSRF tokens, Admin/Analyst/Viewer RBAC, rate limits and audit events.
8. **Feature preparation** — strict one-row CSV validation for the exact EMBER/LAMDA feature schemas; no APK or binary execution.
7. **Web interface** — responsive same-origin dashboard served by FastAPI with local CSS/JavaScript assets; no separate frontend build is required.

## Trust boundaries

- Feed responses are untrusted and validated before use.
- External AI providers are not configured in this MVP. Add a provider only behind the router and data-loss controls.
- Read-only intelligence tools are separated from local metadata writes.
- Human review remains required before remediation is applied to any real system.

## Planned sequence

- M0: safe project scaffold, metadata validation, feed connectors, tests and CI.
- M1: dataset import/quality checks for EMBER feature-only data.
- M2: baseline malware classifier trained only on static feature vectors; model card and temporal holdout evaluation.
- M3: optional LLM router and specialist agents, with a narrow MCP allowlist.
- M4: responsive web dashboard, multi-user authentication, RBAC, CSRF, audit dashboard and guarded feature-data preparation implemented; hosting provider/database provisioning and first-admin bootstrap remain deployment steps.
