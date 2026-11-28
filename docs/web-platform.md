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

## Google Sign-In and account linking

The login page offers optional Google Identity Services sign-in. The official Google button is shown only when `/api/auth/providers` reports Google enabled and both the configured client ID and `google_identities` storage are ready. Its surrounding Nanou presentation is custom; Google's interactive button and brand remain provider-controlled.

- `GET /api/auth/providers` reports whether the client ID and identity storage are ready.
- `POST /api/auth/google` verifies the ID token server-side against the configured client ID, Google issuer and verified email. A new identity is an inactive, unapproved Viewer and receives no session until an Admin approves it. Existing password accounts are not linked automatically.
- `GET /api/auth/google/status` and `POST /api/auth/google/link` require authentication. Linking requires a matching verified Google email and rejects an identity already linked elsewhere.

For PR #18 Preview, add the Google OAuth Web Client's Authorized JavaScript origin `https://nanou-cyber-defense-ai-git-feat-auth-google-categ-90207d-nanou3.vercel.app` and set its public Client ID only in Vercel Preview `NANOU_GOOGLE_CLIENT_ID`. Keep Production OAuth separate until release approval. This GIS ID-token flow does not require a Google Client Secret in browser code. Never store provider secrets in Git, HTML, JavaScript, browser storage or chat.

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


## Google Sign-In and registration

Google Identity Services is enabled only when `NANOU_GOOGLE_CLIENT_ID` contains the Web application OAuth client ID created in Google Cloud. For the PR #18 Preview, add the exact branch origin `https://nanou-cyber-defense-ai-git-feat-auth-google-categ-90207d-nanou3.vercel.app` to Authorized JavaScript origins and set the public client ID as a Vercel **Preview-only** environment variable. Do not set the Production value until the Production release is explicitly approved. Use separate OAuth Web clients for Preview and Production where practical; the Production origin is `https://nanou-cyber-defense-ai.vercel.app`. The client ID is public; this Google Identity Services ID-token flow does not require putting a Google Client Secret in browser code. The backend verifies ID tokens using Google's signing keys and the configured audience.

For the current PR #18 Preview only, `public.google_identities` has been created in the isolated Neon Preview database `nanou_preview`. It is owned by `nanou_preview_app`; the restricted `nanou_preview_runtime` role has DML access only and no `TRUNCATE`. Production schema and roles were not changed. Production migration must continue to use its dedicated reviewed migration login/owner, never `nanou_preview_app`.

A first Google sign-in creates an inactive, unapproved Viewer request. Google identities are keyed by Google's immutable OIDC `sub` claim, not by email alone. An email already belonging to a password account cannot be claimed by Google automatically: the owner must first sign in with the existing password and explicitly link the same verified email from account settings. A linked Google identity can establish a session only when the local account is approved and active. Google identity never creates an Admin or bypasses the existing RBAC approval process.

Before enabling Google on PostgreSQL, apply `scripts/migrations/20261127_google_identities.sql` through `NANOU_MIGRATION_DATABASE_URL`; the script sets `nanou_migration_owner` and relies on its default ACL for the restricted `nanou_runtime` role. Verify `SELECT`/`INSERT` access before enabling the feature. Do not run DDL from the serverless runtime account. The Google identity table is an optional schema component: a missing table does not block startup or password login, and `/api/auth/providers` keeps Google disabled until the migration is present. SQLite creates the optional table for tests and local development. If the client ID is absent, the login page explains that Google OAuth setup is still required and password login remains available.

The public entry page shows login first. Detailed password registration is available through its explicit link. After authentication, the dashboard shows broad categories; each category loads its detail panels on demand. `GET /api/auth/providers` exposes only whether the provider is enabled, a reason when disabled, and the public OAuth client ID; `POST /api/auth/google` requires the same-origin CSRF token and never stores the raw Google credential. The login page CSP explicitly allows the documented Google GIS script, frame, connect and stylesheet origins; its Referrer-Policy and COOP headers are scoped to the sign-in page to support the popup flow without relaxing unrelated API responses.
