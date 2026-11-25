# Architecture

## Components

1. **API layer** — FastAPI exposes health, CVE/KEV lookups, metadata records, and the MCP tool catalog.
2. **Connectors** — fixed-origin, read-only clients for NVD and CISA KEV. No user-supplied URL is fetched.
3. **Agents** — small, composable defensive agents. The current triage agent prioritizes known-exploited CVEs and CVSS scores.
4. **Malware feature pipeline** — accepts SHA-256 identifiers, labels, provenance and numeric pre-extracted features. It does not accept or execute binaries.
5. **MCP registry** — describes available tools and checks capabilities before a caller may use a tool. No arbitrary shell or remote-control tool is registered.
6. **Storage** — SQLite metadata store under the user's data directory, outside the Git checkout.

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
- M4: authenticated UI and audit dashboard.
