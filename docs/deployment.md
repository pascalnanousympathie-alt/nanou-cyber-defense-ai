# Hosting, security and deployment runbook

## Current environments

The application is a FastAPI web platform deployed through Vercel. Preview and Production are separate environments and use separate Neon PostgreSQL projects and separate sensitive `NANOU_RUNTIME_DATABASE_URL` values. Do not copy a database URL between environments or place it in Git, screenshots, CI logs or chat.

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
- The web runtime `NANOU_RUNTIME_DATABASE_URL` must use a separate login role that is not database/schema/table owner and has no `CREATEDB`, `CREATEROLE`, `BYPASSRLS`, `TRUNCATE` or schema `CREATE`. It needs only the DML required by the app (SELECT/INSERT/UPDATE/DELETE) and sequence USAGE/SELECT. Verify grants on a restored copy before using this in Production.
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


## Latest candidate validation and Preview status (2026-11-26)

This section supersedes older PR candidate status in this runbook.

Current PR #3 head: `90439511a937d74ca3079feac32c4b3d3e90cd4a`, base PR #1 / `feat/web-platform` at `62f0b42bcec2a096186a84e18029048f3ce320da`. PR #3 remains Draft/Open, mergeable and unmerged; it is 59 commits ahead / 0 behind. PR #1 remains Draft/Open to `main`.

Latest GitHub Actions validation on current head:
- CI run [45793720638](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45793720638): **PASS** — Ruff lint, Ruff format, **123 passed / 4 skipped**, ML smoke **13 passed**, pip-audit **no known vulnerabilities found**.
- Security run [45793720747](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45793720747): **PASS** — Gitleaks no leaks; CodeQL Python and JavaScript/TypeScript passed and uploaded SARIF.

### Runtime role model proof

The current candidate has no PostgreSQL DDL during application startup:
- SQLite still initializes schema for local development/tests.
- PostgreSQL startup checks required `public` tables and columns, then uses DML to ensure the one-time bootstrap-state row. Missing tables/columns fail closed with a startup error.
- Initial PostgreSQL schema creation is a separate command, `python -m nanou_cyber_ai.storage.bootstrap`, requiring the protected `NANOU_MIGRATION_DATABASE_URL` environment variable. This creates missing initial tables only; it is not an ALTER/schema-upgrade system.
- In the isolated Neon restore-test project, a `NOLOGIN` runtime probe role with SELECT/INSERT/UPDATE/DELETE and sequence privileges passed a `SET ROLE` capability check and INSERT→UPDATE→DELETE smoke. It had no superuser, CREATEROLE, CREATEDB, BYPASSRLS, database/schema CREATE or TRUNCATE; no test row remained. This is a prototype validation, not a login role configured in Vercel or Production.

### Integrated Preview deployment

A Vercel Git Preview for branch `fix/admin-password-rotation` is **READY**:
- Deployment: `dpl_HSoSTJv8aFcudRrLBtJw7XskY2PW`.
- URL: https://nanou-cyber-defense-ai-git-fix-admin-password-rotation-nanou3.vercel.app/
- Deployed commit: `ad2f668c8323996a16366ade5b4f69f652f8d9e4`.
- The current PR #3 head is 11 commits ahead. Comparing the deployed commit with current head shows only documentation, tests, and small non-runtime bootstrap CLI error-handling changes; the dashboard, API, auth, database runtime verification, CSS and JavaScript application source are unchanged.
- Live Opera smoke checks on that Preview:
  - `/ready`: `{"status":"ready","database":"postgresql"}`.
  - `/api/auth/me`: `authenticated:false`, `user:null`, `bootstrap_required:false` in the signed-out browser.
  - Unauthenticated `/api/admin/users`: denied with `Sign in with an approved account.`.
  - Dashboard screenshot confirms the deep-black / emerald-cyan HUD, grouped menu, dimensional hero typography and shield graphic.
- This is a protected Preview, not Production. Owner Admin login, password-change submission and live Viewer/Analyst acceptance remain unverified because the connected browser is signed out.

Vercel returned HTTP 402 resource `api-deployments-free-per-day` when a forced API deployment was requested (more than 100 deployments and retry-after 86,400 seconds). The Git-linked Preview above was automatically built and is READY; a read-only lookup for the exact current head `9043951` returned zero deployments. No CLI bypass, plan upgrade or paid quota change was used. The current READY Preview is suitable for testing the unchanged application source, but it is not an exact build of the latest docs/tests HEAD.



## 2026-11-26 follow-up — verified Production restore and runtime-role preparation

This section supersedes the earlier statements above that no Production snapshot or runtime login role exists. The Production application deployment itself has NOT been changed.

### Backup and restore drill

- Created Neon manual snapshot prod-pre-hardening-2026-11-26 from Production default branch br-damp-fog-bi0lzjf4.
- Restored it into a separate branch prod-restore-drill-20261126 (br-little-sound-bipv6bjm) in the same Production Neon project, with finalize=false. The Production main branch and its compute were not replaced or restarted.
- Compared source and restored branch: all 60 public schema columns match; row counts match for the populated application tables (audit_events=2, auth_attempts=4, platform_state=1; other application tables are empty). This proves branch snapshot/restore fidelity for the captured state. It does not prove external off-provider disaster recovery or an independent export archive.
- A restore-only login role nanou_runtime_restore_probe passed PostgreSQL capability checks and INSERT→UPDATE→DELETE smoke against the restored copy. It has login, DML and sequence USAGE/SELECT; no superuser, CREATEROLE, CREATEDB, BYPASSRLS, database/schema CREATE or TRUNCATE. The probe row was deleted; zero leftovers.

### Production least-privilege runtime role prepared

- Created Production PostgreSQL login role nanou_runtime on main, without changing the existing nanou_app role or its ownership/privileges.
- Direct role checks passed: login=true, superuser=false, CREATEROLE=false, CREATEDB=false, BYPASSRLS=false, database CONNECT=true, database CREATE=false, public schema USAGE=true, public schema CREATE=false; SELECT/INSERT/UPDATE/DELETE on the nine app tables; no TRUNCATE; sequence USAGE/SELECT.
- Stored its connection string only in Vercel's sensitive Production NANOU_RUNTIME_DATABASE_URL variable. The legacy NANOU_DATABASE_URL remains unchanged for rollback. No secret value was displayed or written to Git.
- The current Production deployment is commit db4fa6a7c059467b8728468425d63ce78414ef5d; its settings code does not yet support NANOU_RUNTIME_DATABASE_URL. Therefore the new role/variable is prepared but NOT active in the running Production deployment. Do not deploy or switch credentials until the reviewed candidate is promoted with a controlled rollback.

### Preview runtime credential prepared

- Stored the dedicated nanou_preview_runtime connection string in the existing sensitive Preview NANOU_RUNTIME_DATABASE_URL variable. It points only to the dedicated Preview Neon project/branch; Production and Preview credentials remain separate.
- Existing Vercel deployment instances may require a new Git-linked Preview deployment before the updated environment value is consumed. No deployment quota bypass or new deployment request was made.

### Remaining blockers / constraints

- Neon Free manual snapshot allowance is limited; this is a single manual snapshot/restore drill, not an automatic recurring backup schedule or external offsite copy. Keep the snapshot and restore branch; do not create repeated snapshots or consume additional quota without checking retention/allowance.
- Neon Free cannot enable the Production default branch protection while the account's protected-branch allowance is exhausted. No other service branch was unprotected and no paid plan was purchased.
- Production nanou_app still has elevated privileges and remains the live credential until a reviewed, exact-head candidate is deployed and validated. Do not revoke it before a tested cutover/rollback window.
- Production deployment remains on the old settings implementation; Production is still not approved for promotion/cutover.

## Latest verified Production and integration status — 2026-11-26

- `main` HEAD is `fe47b815fa90bd2bacd06d4ab4e139e874fce88b` (PR #1 and PR #10 merged). PR #3 and PR #4 remain Draft/Open; their password-rotation/schema-verification and backup-workflow hardening are being prepared in a separate clean integration clone, not yet merged.
- Production environment metadata confirms separate sensitive `NANOU_RUNTIME_DATABASE_URL` and `NANOU_AUDIT_HMAC_KEY` entries; secret values were not read. The current `main` code uses the runtime role selector and keyed HMAC fingerprints.
- Production backup automation is active on `main`: secret name `NANOU_BACKUP_DATABASE_URL` exists; runs `45850155507` and `45852927966` succeeded. The latest encrypted artifact passed checksum, authenticated decryption, `pg_restore --list`, and an isolated local PostgreSQL restore (9 tables / 60 columns). Neon restore of that exact artifact PASSes on isolated branch `br-little-sound-bipv6bjm`; a second offline private-key recovery copy remains outstanding.
- Production deployment remains on old commit `46afde6042841715364f416623a416022a8476d1`. A deployment request for current `main` was blocked by Vercel 402 `api-deployments-free-per-day`; no quota/billing/SSO changes were made.
- `nanou_runtime` has DML on nine tables and sequence USAGE/SELECT only; it has no schema CREATE or TRUNCATE. `nanou_migration_owner` is NOLOGIN. `nanou_app` still owns the Production database and tables. No ownership transfer or credential retirement until the restricted runtime candidate is deployed, verified, and rollback is proven.
- Production Admin bootstrap and live owner/Viewer/Analyst acceptance remain outstanding. Keep Vercel SSO enabled; no public launch is approved.
