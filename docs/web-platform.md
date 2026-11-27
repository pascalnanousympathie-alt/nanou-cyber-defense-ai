# Nanou Cyber Defense AI — Web platform

The application is a responsive browser-based platform served directly by FastAPI. It does not require an Android APK or a separate frontend build.

## Visual design system

The dashboard uses an original cyber-operations visual system: deep black surfaces, emerald/cyan accents, grid/HUD texture, terminal-inspired monospace labels, subtle glow and layered CSS text shadows for dimensional headings. The sidebar groups navigation by workspace, access/governance, threat intelligence, static analysis, defensive simulations and integrations.

The visual treatment is CSS-only and uses system font fallbacks; it does not download font assets or rely on a heavy WebGL background. Reduced-motion preferences, visible keyboard focus, responsive navigation and readable contrast are preserved. The design takes broad cyber-terminal visual cues only; product branding and layout are original.

The “Tabletop simulation” menu is a local defensive exercise/report feature, not an exploit runner. “Static feature analysis” accepts pre-extracted CSV feature rows, not APK binaries.

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

State-changing requests require a double-submit CSRF token and same-origin validation when an Origin header is present. The app applies request-size limits, auth rate limits, restrictive CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, and HSTS on HTTPS.

Roles:
- `admin` — approve/manage users, assign roles, view audit events, manage Attack Simulation scopes, and use analyst features.
- `analyst` — prepare feature data, run inference, add metadata, view intelligence, and create local Attack Simulation tabletop reports (cannot add or revoke target scopes).
- `viewer` — read permitted intelligence and metadata.

The first account is created through one-time Administrator bootstrap. It requires a random `NANOU_BOOTSTRAP_TOKEN` of at least 32 characters stored in the hosting secret manager and entered once in the protected bootstrap form. Once claimed, bootstrap remains disabled; changing the token does not reopen it. The dedicated Preview already has its first active/approved Admin and `bootstrap_claimed=true`; the Production database currently has zero users. Public registrations remain pending until an Administrator approves them. There is no email verification or self-service password reset yet; account approval and recovery are administrator-managed.

Audit events cover bootstrap, registration, login/logout outcomes, rate-limit events, account changes, feature preparation, and successful inference. Raw IP addresses are not stored; only a digest is retained.

## Admin-to-Termux read-only pairing

An authenticated Admin may create a one-time Termux pairing code from the account-governance panel. The code expires after 90 seconds and is consumed atomically once. Exchange issues a separate admin:bridge:read bearer for 15 minutes; the token is hashed in the existing api_keys table, held only in the Termux helper's memory, and never exports the browser session cookie or password.

The bridge exposes only Admin identity, user-list and audit-list reads, at 30 requests per minute. It cannot approve users, change roles, disable accounts, modify metadata, access Developer API functions, or perform arbitrary host operations. A new pairing revokes earlier bridge/pairing tokens for that Admin; password rotation and role/active changes also revoke the bridge. The local helper accepts only ping, whoami, users and audit over a 0600 Unix socket in a dedicated 0700 directory under the Termux home folder. See [Admin-to-Termux pairing](admin-session-pairing.md).

## Local development

~~~bash
python -m pip install -e ".[dev]"
uvicorn nanou_cyber_ai.api:app --host 127.0.0.1 --port 8000
~~~

Without either PostgreSQL URL, local development uses SQLite at `NANOU_DATA_DIR/malware_metadata.sqlite3`. On Vercel/AWS Lambda, the application requires `NANOU_RUNTIME_DATABASE_URL` and fails closed if it is absent; it never falls back to the legacy credential.

## PostgreSQL schema and runtime privileges

The hosted PostgreSQL runtime is schema-verify-only: application startup checks that required `public` tables and columns exist, then initializes the bootstrap-state row with normal DML. It does not execute PostgreSQL DDL. Local SQLite development/tests still create their own schema.

Use a separate operator/migration connection for the initial PostgreSQL schema:
`NANOU_MIGRATION_DATABASE_URL` must be supplied through a protected one-off operator environment, then run:

```bash
python -m nanou_cyber_ai.storage.bootstrap
```

The bootstrap command uses `metadata.create_all(checkfirst)` to create missing initial tables and an idempotent bootstrap-state insert. It does not alter existing columns or constraints, so it is not a replacement for reviewed migrations. Future changes to an existing schema require explicit migration SQL and a restore/rollback plan.

The application runtime's `NANOU_DATABASE_URL` must point to a separate restricted login role with only the required DML privileges and sequence usage. It must not own the database/schema/tables and must not have CREATE, TRUNCATE, CREATEROLE, CREATEDB or BYPASSRLS capability. Test this exact role on a restored copy before changing any hosted environment.

## PostgreSQL hosting

Set `NANOU_RUNTIME_DATABASE_URL` to the dedicated PostgreSQL project using the least-privilege runtime role. The legacy `NANOU_DATABASE_URL` is only a local-development fallback. The application requires TLS and uses a small connection pool. PostgreSQL runtime startup performs no schema DDL; use the separate migration-owner role for reviewed schema migrations. Do not reuse a database belonging to LudoMada, Mada Commander, Nanou Browser or another unrelated service.

## Safe feature-data preparation

The preparation endpoint accepts CSV text only, capped at 1 MiB and exactly one data row. Headers must match the selected model schema, in order:
- EMBER2024: 2,568 numeric columns named `ember_feature_0000` through `ember_feature_2567`.
- LAMDA: 4,561 columns named `feat_0` through `feat_4560`, signed int8 values from -128 through 127.

Optional metadata columns are `sha256` and `label`; these are validated but excluded from model input. Unknown, missing, duplicate, reordered or extra columns, multiple rows, non-finite values and out-of-range LAMDA values are rejected. CSV content is not persisted.

This is not an APK scanner. The platform does not yet parse APK binaries or extract their features. A genuine APK-to-feature extractor must be separately implemented and validated against the exact training schema before claiming direct APK scanning.

## Vercel deployment

The repository includes `index.py`, `requirements.txt`, `.python-version`, and `vercel.json`. Vercel project protection is configured for all deployments; the first Administrator must be created while that protection remains enabled.

The Vercel Hobby plan is free but restricted to personal/non-commercial use. Do not use it for commercial or third-party service delivery. See [deployment runbook](deployment.md).

## Before public launch

Preview currently has a dedicated PostgreSQL project, its own sensitive database credential, one-time Admin bootstrap and an encrypted backup/restore drill in an isolated test project. This is not Production evidence.

Production currently has nine application tables but zero users. The Production runtime database role owns the database and all tables and has excessive role/table privileges, no snapshots or automatic snapshot schedule were present, and the default branch could not be protected on the current Neon Free plan. Do not promote Production until these findings are resolved on a tested copy and a backup/rollback path is proven.

Before public use:
1. Separate a schema migration owner from a least-privilege application runtime role, test grants/ownership on a restored database copy, and verify all application queries and migration steps.
2. Complete owner-browser Admin acceptance and live Viewer/Analyst approval, role boundaries, logout and re-login checks.
3. Establish and restore a Production backup; document RPO/RTO, retention, billing and quota. Do not create paid snapshots or upgrade a plan without approval.
4. Resolve Production branch/deployment protection without disabling Vercel SSO or weakening other projects.
5. Review monitoring, incident response, SAST/secrets/dependency alerts and independent security findings.
6. Complete model-artifact integrity and separate validation-set threshold checks before claiming malware inference readiness.
7. Implement email verification and self-service recovery before accepting public registrations at scale.

Vercel Hobby is restricted to personal/non-commercial use under its Terms of Service. Select a plan appropriate to the intended service before public/commercial operation. See [deployment runbook](deployment.md).

Do not expose an unprotected public deployment or migrate Production data until its database access, backup/restore, deployment protection and operational controls are separately verified.

## Additional account and request hardening (PR #3 candidate)

The follow-up `fix/admin-password-rotation` branch adds `POST /api/auth/password`. It requires an authenticated user, CSRF validation, the current password and a different 12+ character replacement. On success, all previous sessions for the account are revoked and only the current browser receives a new session. Logout revokes the server-side session.

The candidate also uses purpose-separated HMAC-SHA-256 values for audit IP and email/IP rate-limit fingerprints. A dedicated `NANOU_AUDIT_HMAC_KEY` can be configured as a 64–128 character hosting secret; until configured, hosted environments derive a separate key from their environment-specific PostgreSQL secret, while local development uses a process-local random key. Key rotation changes the fingerprints and restarts rate-limit windows.

The candidate enforces a 2 MiB request-body ceiling at the ASGI receive stream so both declared and chunked request bodies are bounded without pre-consuming the body. PR #3 remains Draft/Open until post-sync CI and security checks pass.
