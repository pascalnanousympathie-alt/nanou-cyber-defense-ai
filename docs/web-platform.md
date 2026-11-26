# Nanou Cyber Defense AI — Web platform

The application is a responsive browser-based platform served directly by FastAPI. It does not require an Android APK or a separate frontend build.

## Web interface and APIs

- `/` — responsive Malagasy dashboard for mobile and desktop browsers.
- `/health` — process health.
- `/ready` — readiness check; requires a reachable durable database on hosted deployments.
- `/api/auth/csrf` — issues the CSRF cookie/token for browser forms.
- `/api/auth/me` — current account and first-administrator bootstrap status.
- `/api/auth/bootstrap` — creates the one-time first Administrator.
- `/api/auth/register` — creates a pending Viewer account.
- `/api/auth/login`, `/api/auth/logout` — password login and server-side session revocation.
- `/api/admin/users`, `/api/admin/users/{id}` — Admin-only approval, role changes and deactivation.
- `/api/admin/audit` — Admin-only audit-event listing.
- `/api/cve/{cve_id}` — read-only NVD vulnerability lookup.
- `/api/kev` — read-only CISA Known Exploited Vulnerabilities feed.
- `/api/mcp/tools` — scope-limited MCP tool inventory.
- `/api/malware/metadata` — authenticated malware-hash metadata.
- `/api/malware/inference/status` — model integrity/schema status.
- `/api/malware/features/prepare/{dataset_id}` — validate one pre-extracted CSV feature row.
- `/api/malware/inference` — Admin/Analyst-only classification of a validated numeric vector.
- `/api/attack/scopes` — Admin-managed target allowlist with declared authorization basis and expiry.
- `/api/attack/scopes/{scope_id}/revoke` — Admin-only soft revocation of an allowlist entry.
- `/api/attack/simulations` — Admin/Analyst local-only tabletop report creation and history.
- `/docs` — FastAPI OpenAPI documentation.

## Authentication and access control

Passwords use Argon2id. Browser sessions use opaque HttpOnly cookies with SameSite=Strict and Secure on HTTPS; only token hashes are stored. Sessions have a configurable absolute expiry (default 12 hours). Logout revokes the server-side session.

State-changing requests require a double-submit CSRF token and same-origin validation when an Origin header is present. Request bodies are bounded to 2 MiB while streaming, including requests without `Content-Length`; oversized and malformed declared lengths are rejected before route handlers run. The app also applies auth rate limits, restrictive CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, and HSTS on HTTPS.

Roles:
- `admin` — approve/manage users, assign roles, view audit events, manage Attack Simulation scopes, and use analyst features.
- `analyst` — prepare feature data, run inference, add metadata, view intelligence, and create local Attack Simulation tabletop reports (cannot add or revoke target scopes).
- `viewer` — read permitted intelligence and metadata.

The first account is created through one-time Administrator bootstrap. It requires a random `NANOU_BOOTSTRAP_TOKEN` of at least 32 characters stored in the hosting secret manager and entered once in the protected bootstrap form. Once claimed, bootstrap remains disabled; changing the token does not reopen it. The current dedicated Preview already has its first Admin and `bootstrap_claimed=true`. Public registrations remain pending until an Administrator approves them. There is no email verification or self-service password reset yet; account approval and recovery are administrator-managed.

Audit events cover bootstrap, registration, login/logout outcomes, rate-limit events, account changes, feature preparation, and successful inference. Raw IP addresses and email-derived rate-limit identifiers are not stored; keyed HMAC-SHA-256 fingerprints are used with purpose separation. Configure a stable, high-entropy `NANOU_AUDIT_HMAC_KEY` (64–128 characters) in the hosting secret manager when available. If it is not configured, hosted environments derive a separate HMAC key from their environment-specific PostgreSQL secret; local development uses a process-local random key. Changing either key rotates rate-limit fingerprints, so active rate-limit windows naturally restart.

## Local development

~~~bash
python -m pip install -e ".[dev]"
uvicorn nanou_cyber_ai.api:app --host 127.0.0.1 --port 8000
~~~

Without `NANOU_DATABASE_URL`, local development uses SQLite at `NANOU_DATA_DIR/malware_metadata.sqlite3`. This fallback is blocked on Vercel/AWS Lambda because their local filesystems are not durable.

## Security validation

The pull-request CI runs Ruff lint/format, the application pytest suite, ML smoke tests, and `pip-audit` against installed third-party Python dependencies. The development dependency floor requires `pytest>=9.0.3`. The latest verified PR run passed **116 tests (4 skipped)**, **13 ML smoke tests**, and dependency audit reported **no known vulnerabilities**.

The separate security workflow runs:
- Gitleaks 8.30.1 on the PR range and all fetched Git refs/history. Latest result: **No leaks detected**.
- GitHub CodeQL analysis for **Python** and **JavaScript/TypeScript**. Both analyses completed and uploaded successfully; the Code Scanning API returned **0 open alerts** for the reviewed branch at the time checked.

These checks are automated static/dependency scans, not a dynamic penetration test or independent threat-model review. No container-image scan is claimed for the current serverless deployment. Complete a separate operational/security review before public or Production use.

## PostgreSQL hosting

Set `NANOU_DATABASE_URL` to a dedicated PostgreSQL project. The application requires TLS and uses a small connection pool. Do not reuse a database belonging to LudoMada, Mada Commander, Nanou Browser or another unrelated service.

## Safe feature-data preparation

The preparation endpoint accepts CSV text only, capped at 1 MiB and exactly one data row. Headers must match the selected model schema, in order:
- EMBER2024: 2,568 numeric columns named `ember_feature_0000` through `ember_feature_2567`.
- LAMDA: 4,561 columns named `feat_0` through `feat_4560`, signed int8 values from -128 through 127.

Optional metadata columns are `sha256` and `label`; these are validated but excluded from model input. Unknown, missing, duplicate, reordered or extra columns, multiple rows, non-finite values and out-of-range LAMDA values are rejected. CSV content is not persisted.

This is not an APK scanner. The platform does not yet parse APK binaries or extract their features. A genuine APK-to-feature extractor must be separately implemented and validated against the exact training schema before claiming direct APK scanning.

## Vercel deployment

The repository includes `index.py`, `requirements.txt`, `.python-version`, and `vercel.json`. Vercel project protection is configured for all deployments. The dedicated Preview's first Administrator has already been created; a separate new environment must complete its own one-time bootstrap with its own secret.

The Vercel Hobby plan is free but restricted to personal/non-commercial use. Do not use it for commercial or third-party service delivery. See [deployment runbook](deployment.md).

## Before public launch

For the current Preview, a dedicated Neon PostgreSQL project, Preview-only database secret, first Admin bootstrap, encrypted backup/restore drill and protected HTTPS deployment have been verified. They are not Production evidence.

Before Production or public use:
1. Prepare a separate Production PostgreSQL migration, least-privilege role, backup/restore drill and rollback plan.
2. Complete owner-browser Admin acceptance and live Viewer/Analyst approval, permissions and logout checks.
3. Review hosting-plan terms, data retention, quotas, rate limits, logging and incident-response ownership.
4. Select and verify the ML decision threshold on a separate validation set; deploy only a trusted, SHA-256-verified model artifact.
5. Implement email verification and self-service recovery before accepting public registrations at scale.
6. Complete SAST, secret scanning, container scanning (if applicable), and an independent security review.

Do not expose an unprotected public deployment or use Production data until its database, access, backup/restore and operational controls are separately verified.
