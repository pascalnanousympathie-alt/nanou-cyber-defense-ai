# Hosting, security and deployment runbook

## Current environments

The application is a FastAPI web platform deployed through Vercel. Preview and Production are separate environments and use separate Neon PostgreSQL projects and separate sensitive `NANOU_DATABASE_URL` values. Do not copy a database URL between environments or place it in Git, screenshots, CI logs or chat.

- Repository: `pascalnanousympathie-alt/nanou-cyber-defense-ai`.
- Current candidate branch: `feat/web-platform`, PR #1 → `main`.
- Admin password and HMAC hardening branch: `fix/admin-password-rotation`, PR #3 → `feat/web-platform`.
- Vercel project: `nanou-cyber-defense-ai`, team `nanou3`.
- Vercel Authentication remains enabled for **All Deployments**. The Preview is protected; this runbook does not authorize SSO removal or Production promotion.

### Preview environment

- Dedicated Neon project: `nanou-cyber-defense-preview` (`young-snow-19049684`), PostgreSQL 17.
- Dedicated Preview branch: `preview` (`br-long-field-bianlzu3`).
- Preview schema has nine application tables and is connected through its separate app role.
- First Administrator was already created in this Preview. It is active/approved with role `admin`; `bootstrap_claimed=true`. Do not reset bootstrap or recreate this account.
- Encrypted post-rotation Preview backup was restored to a separate isolated Neon test project. The drill verified seven application tables, one Admin, four audit events and the bootstrap flag. The backup intentionally omits ephemeral `auth_sessions` and `auth_attempts`; it is not a complete live-session recovery image.
- Preview PITR history retention is six hours. No recurring snapshot schedule is configured. No paid manual snapshot was created.

Latest UI Preview:
- Deployment: **READY**, commit `016fcd1766b69e0bfa85844630323f981e85329d`.
- URL: https://nanou-cyber-defense-n51j1uvig-nanou3.vercel.app/
- `/ready`: `{"status":"ready","database":"postgresql"}`.
- `/api/auth/me` from the connected signed-out browser: `authenticated:false`, `user:null`, `bootstrap_required:false`.
- Unauthenticated `/api/admin/users`: correctly denied with `Sign in with an approved account.`.
- The owner’s authenticated browser acceptance and live Viewer/Analyst account acceptance remain pending; automated tests are not a substitute for those owner-session checks.

### Production environment — read-only audit

Production Neon project `nanou-cyber-defense-ai` (`cold-resonance-28231813`), PostgreSQL 17.12:
- Default branch `main` (`br-damp-fog-bi0lzjf4`) is **not protected**.
- Database `nanou_cyber_defense` contains nine application tables and is approximately 7.88 MiB.
- Current Production row counts: `users=0`, `auth_sessions=0`, `api_keys=0`, `malware_metadata=0`, `attack_scopes=0`, `attack_simulations=0`, `audit_events=2`, `auth_attempts=4`, `platform_state=1`.
- The live database role `nanou_app` owns the database and all application tables, has `CREATEROLE`, `CREATEDB` and inherited `BYPASSRLS` capability through `neon_superuser`; it also has broad table privileges including `TRUNCATE`. This is not an acceptable least-privilege runtime role for a public Production service.
- The candidate web runtime now verifies required PostgreSQL tables and columns at startup and performs no PostgreSQL DDL. SQLite still initializes automatically for local development/tests. The initial PostgreSQL schema bootstrap is a separate one-off command using `NANOU_MIGRATION_DATABASE_URL`.
- No Neon snapshots or automatic snapshot schedule were present at the time of audit. PITR history retention is six hours.
- Neon Free rejected enabling protection for the Production default branch because the maximum protected-branch allowance was already reached. No other branch was unprotected, and no paid upgrade was performed.
- No SQL changes, privilege changes, migrations, Production deployment or Production data writes were performed during this audit.

**Production is not approved for promotion yet.** The runtime database role must be separated from the schema owner/migration role; least-privilege grants and ownership must be verified on a restored/test copy first. A proven Production backup/restore path and branch/deployment protection strategy are also required.

## CI and security validation

Latest PR #1 validation for commit `016fcd1766b69e0bfa85844630323f981e85329d`:

- CI run [45788575840](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45788575840): **PASS**.
  - Ruff lint and format: PASS (71 files formatted).
  - Pytest: **110 passed / 4 skipped**.
  - ML smoke: **13 passed**.
  - `pip-audit`: **No known vulnerabilities found**.
- Security scan run [45788575928](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45788575928): **PASS**.
  - Gitleaks 8.30.1 scanned the PR range and fetched Git refs/history: **No leaks detected**.
  - CodeQL Python and JavaScript/TypeScript analyses completed and uploaded SARIF.
  - GitHub Security alert overview was not independently inspected because the connected GitHub browser session is signed out; do not infer a zero-alert count.

CI pins GitHub Actions checkout/setup-python to v6/Node 24 and disables persisted checkout credentials. Dependency scanning covers installed third-party Python packages. These checks are not a dynamic penetration test, full independent threat model or container-image scan.

## Database and migration policy

The current candidate separates schema ownership from runtime behavior:

- PostgreSQL application startup verifies the required `public` tables and columns; it does **not** call `metadata.create_all` or attempt schema DDL.
- SQLite remains self-initializing only for local development and tests.
- Initial PostgreSQL schema bootstrap is a separate one-off command:
  `python -m nanou_cyber_ai.storage.bootstrap`.
- That command requires `NANOU_MIGRATION_DATABASE_URL`, stored only in a protected operator/migration environment. Do not put its raw value in Git, shell history, chat or CI logs.
- The bootstrap uses SQLAlchemy `create_all(checkfirst)` plus an idempotent bootstrap-state insert. It creates missing initial tables but does not ALTER existing tables; it is **not** a schema-upgrade/migration engine. Future schema changes require explicit, reviewed migration SQL.
- The web runtime `NANOU_DATABASE_URL` must use a separate login role that is not database/schema/table owner and has no `CREATEDB`, `CREATEROLE`, `BYPASSRLS`, `TRUNCATE` or schema `CREATE`. It needs only the DML required by the app (SELECT/INSERT/UPDATE/DELETE) and sequence USAGE/SELECT. Verify grants on a restored copy before using this in Production.
- The restore-test project has a successful `NOLOGIN` prototype proving those DML/sequence privileges without CREATE/TRUNCATE/BYPASSRLS. This prototype is not a Vercel login credential and has not been connected to either environment.

- Hosted/serverless runtime must use a durable PostgreSQL connection. SQLite fallback is local development/test only.
- Introduce explicit, reviewed schema migrations; do not rely on app startup `metadata.create_all` as a substitute for Production migration management.
- Use distinct roles: an owner/migration role for schema changes and a restricted runtime role for normal application queries. Test the exact DDL, grants, sequences and application behavior on an isolated restored copy before considering Production.
- Confirm backup coverage, restore time, retention, quota, connection permissions and rollback before any Production migration.
- Keep Preview and Production database credentials separate and sensitive. Never print or reveal their values.
- Vercel Hobby is restricted to personal/non-commercial use under its Terms of Service. Confirm plan suitability before any public or commercial service: https://vercel.com/legal/terms
- Neon Free has usage and branch-protection constraints. Manual snapshot storage may incur a charge; do not create paid snapshots or upgrade plans without explicit cost approval.

## Functional scope and limitations

The platform currently provides defensive vulnerability intelligence, CISA KEV, scoped MCP inventory, account/RBAC governance, local tabletop simulations and pre-extracted static-feature CSV validation/inference when a trusted model is provisioned.

- The malware workflow accepts a single row of validated CSV features; it is **not a direct APK scanner**.
- No APK/executable is uploaded or executed.
- No autonomous exploit, shell, malware execution, destructive remediation or offensive command runner is provided.
- External AI provider integration remains disabled until a secure server-side provider configuration and approved service-to-service access design exist.
- A trusted SHA-256-verified production model artifact and independently validated decision threshold are still required before claiming production malware inference.

## Remaining launch gates

1. Complete owner-browser Admin acceptance and separate live Viewer/Analyst registration, approval, RBAC and logout/re-login acceptance.
2. Design and test separate migration-owner and least-privilege runtime roles on a restored copy; verify application behavior and all DDL privileges.
3. Establish a reliable Production backup/export and restore drill, and document RPO/RTO. Current Production has no snapshots/schedule; Neon branch protection is blocked by the Free plan limit.
4. Resolve Production branch and deployment protection without weakening another service or bypassing SSO.
5. Confirm hosting/database plan terms, quotas, retention, monitoring, alert routing and incident response.
6. Complete independent security review, code-scanning alert review while signed into GitHub, and a documented rollback plan.
7. Integrate PR #3 into the updated `feat/web-platform` branch, rerun combined CI/security scans, then review PR #1 before any merge to `main`.

No Production promotion is permitted by this runbook until these gates are verified and the Production migration/rollback plan is approved.

## Candidate security hardening in PR #3

The follow-up branch `fix/admin-password-rotation` adds authenticated password rotation requiring the current password and CSRF protection, a new password of at least 12 characters, revocation of prior sessions, and a new session only for the browser completing the change. Logout also revokes its server-side session.

The same candidate adds purpose-separated keyed HMAC-SHA-256 fingerprints for IP audit and email/IP rate-limit identifiers, plus an ASGI receive-boundary request-size ceiling of 2 MiB that includes streamed requests without `Content-Length`. Its tests cover password-change failures/success, old-session revocation, logout, HMAC separation and streamed body rejection.

These hardening changes remain in Draft PR #3 until the updated branch has passed its post-sync CI/security runs and the PRs are deliberately integrated. They are not represented as Production changes.


## Latest candidate validation and deployment limit (2026-11-26)

This section supersedes older PR candidate status in this runbook.

Candidate head `125dc8c14acb3179ba320aee6ac4e1fbb6b777c0`, PR #3 → `feat/web-platform`:
- GitHub Actions CI run [45793385104](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45793385104): **PASS** — Ruff lint, Ruff format, pytest, ML smoke and dependency audit.
- The previous full suite count remains **116 passed / 4 skipped**; the newly-added PostgreSQL schema-policy test module adds seven isolated schema/bootstrap tests. The run logs for the latest commit should be used for the exact updated test count before recording it.
- ML smoke: **13 passed**.
- pip-audit: **No known vulnerabilities found**.
- Security run [45793385156](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45793385156): **PASS** — Gitleaks no leaks; CodeQL Python and JavaScript/TypeScript completed successfully and uploaded SARIF.
- PR #3 remains Draft/Open, targets `feat/web-platform`, is mergeable and unmerged. PR #1 remains Draft/Open to `main`.

### Runtime role model proof

The candidate now has no PostgreSQL DDL during application startup:
- SQLite still initializes schema for local development/tests.
- PostgreSQL startup checks the required `public` tables and columns, then uses DML to ensure the one-time bootstrap-state row. Missing tables/columns fail closed with a startup error.
- Initial PostgreSQL schema creation is a separate command, `python -m nanou_cyber_ai.storage.bootstrap`, requiring the protected `NANOU_MIGRATION_DATABASE_URL` environment variable. This is an initial bootstrap only, not an ALTER/schema-upgrade system.
- In the isolated Neon restore-test project, a `NOLOGIN` runtime probe role with SELECT/INSERT/UPDATE/DELETE and sequence privileges passed a `SET ROLE` capability check and a test INSERT→UPDATE→DELETE. It had no superuser, CREATEROLE, CREATEDB, BYPASSRLS, database/schema CREATE or TRUNCATE; no test row remained. This is a prototype validation, not a login role configured in Vercel or Production.

### Preview deployment status

The existing UI-only Preview at https://nanou-cyber-defense-90y9bz97o-nanou3.vercel.app/ remains the latest verified READY interface build. It is not the integrated PR #3 candidate head.

A new Preview deployment for the current branch/head was blocked by Vercel with HTTP 402, resource `api-deployments-free-per-day`, message “more than 100” deployments and retry-after 86,400 seconds. A read-only Vercel query for commit `125dc8c` returned zero deployment records. No CLI bypass, plan upgrade or repeated deployment attempt was used. Treat the integrated password-rotation/database-policy build as **not yet Preview-live** until the limit resets or the owner resolves the team quota.
