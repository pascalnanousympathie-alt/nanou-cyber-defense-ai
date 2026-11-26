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
- Read-only catalog checks confirmed `nanou_runtime` is a separate LOGIN role with no superuser, database/role creation, replication, BYPASSRLS or `neon_superuser` membership. It has DML on all nine application tables, sequence USAGE/SELECT, and no TRUNCATE, REFERENCES, TRIGGER or schema CREATE.
- `nanou_migration_owner` exists as NOLOGIN, but all nine Production tables and both sequences are still owned by `nanou_app`; ownership has not been transferred.
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

- Hosted/serverless runtime must use `NANOU_RUNTIME_DATABASE_URL`, a durable PostgreSQL connection using the least-privilege runtime role. `NANOU_DATABASE_URL` is retained only as a local-development compatibility fallback; hosted runtime fails closed if the runtime URL is missing. SQLite fallback is local development/test only.
- PostgreSQL runtime startup performs no schema DDL; `metadata.create_all` is limited to local SQLite development/tests. Apply explicit, reviewed schema migrations with the migration-owner role before deploying code that needs them.
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
2. Transfer Production table/sequence ownership to the NOLOGIN migration owner through a reviewed, tested migration plan; verify its DDL scope and preserve the existing least-privilege runtime grants.
3. Establish a reliable Production backup/export and restore drill, and document RPO/RTO. Current Production has no snapshots/schedule; Neon branch protection is blocked by the Free plan limit.
4. Resolve Production branch and deployment protection without weakening another service or bypassing SSO.
5. Confirm hosting/database plan terms, quotas, retention, monitoring, alert routing and incident response.
6. Complete independent security review, code-scanning alert review while signed into GitHub, and a documented rollback plan.
7. Integrate PR #3 into the updated `feat/web-platform` branch, rerun combined CI/security scans, then review PR #1 before any merge to `main`.

No Production promotion is permitted by this runbook until these gates are verified and the Production migration/rollback plan is approved.
