# Project Status — Nanou Cyber Defense AI

Last verified: 2026-11-26 (UTC)

## Product scope

Nanou Cyber Defense AI is a defensive cybersecurity web platform. Its current workflows include vulnerability intelligence (NVD/CVE and CISA KEV), scoped MCP tool inventory, account/RBAC governance, AI assistant read-only defensive commands, pre-extracted malware-feature CSV validation, and local defensive tabletop reports.

Safety boundaries:
- No malware or executable upload/execution.
- No autonomous exploit runner, shell/process execution, intrusive scanning, or autonomous remediation.
- The malware feature workflow accepts a pre-extracted CSV row. It is not a direct APK scanner.
- Malware inference requires a trusted SHA-256-verified model artifact; no Production model readiness is claimed.
- Optional external AI-provider calls remain disabled until a safe server-side provider/access model is approved and configured.

## Repository and branches

Repository: pascalnanousympathie-alt/nanou-cyber-defense-ai.

- PR #1: feat/web-platform → main, Draft/Open, mergeable, unmerged. Head: 62f0b42bcec2a096186a84e18029048f3ce320da.
- PR #3: fix/admin-password-rotation → feat/web-platform, Draft/Open, mergeable, unmerged. Head at last verification: 590488b8afebfa740add47dbd8757588c8033634; base: 62f0b42bcec2a096186a84e18029048f3ce320da; 59 commits ahead / 0 behind.
- PR #3 contains PR #1's cyber UI through a normal merge commit. No force-push, no merge into main, and no Production promotion has occurred.

The repository did not contain the historical PROJECT_STATUS / PARALLEL_ORCHESTRATION files; this document and PARALLEL_ORCHESTRATION_RUNBOOK.md are the new coordination references.

## Latest verified UI and Preview

A protected Git Preview is READY:
- Deployment ID: dpl_HSoSTJv8aFcudRrLBtJw7XskY2PW.
- Preview URL: https://nanou-cyber-defense-ai-git-fix-admin-password-rotation-nanou3.vercel.app/
- Deployed Git commit: ad2f668c8323996a16366ade5b4f69f652f8d9e4.

The Preview commit is 11 commits behind current PR #3 head. Git comparison shows those differences are docs, tests and minor bootstrap CLI error handling; the app runtime, auth/API, database runtime verification, CSS and JavaScript application source are unchanged.

Live Opera evidence on this Preview:
- /ready: {"status":"ready","database":"postgresql"}.
- /api/auth/me: authenticated:false, user:null, bootstrap_required:false in the signed-out browser.
- Unauthenticated /api/admin/users: denied with “Sign in with an approved account.”
- Screenshot verifies deep-black/emerald-cyan HUD, grouped navigation, dimensional CSS typography and shield hero.
- Connected browser is signed out. Owner Admin Console/password-change acceptance and live Viewer/Analyst acceptance are not yet verified.

A manual Vercel API deployment request returned HTTP 402 api-deployments-free-per-day (more than 100 deployments, retry-after 24h). The Git-linked Preview above exists and is READY; an exact Preview for the latest docs/test HEAD was not created. No CLI bypass or paid upgrade was attempted. Keep SSO enabled.

## Latest CI and security evidence

On current PR #3 head 590488b8afebfa740add47dbd8757588c8033634:
- CI [45794790570](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45794790570): PASS.
  - Ruff lint and format: PASS.
  - Pytest: 123 passed / 4 skipped.
  - ML smoke: 13 passed.
  - pip-audit: no known vulnerabilities found.
- Security [45794790508](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45794790508): PASS.
  - Gitleaks full-history/refs: no leaks detected.
  - CodeQL Python and JavaScript/TypeScript: PASS, SARIF uploaded.
- GitHub Code Scanning alert overview was not independently inspected from the connected signed-out session. Do not claim zero open alerts.

## Database and Production status

Preview and Production use distinct Neon projects and separate sensitive Vercel database variables.

Production Neon project cold-resonance-28231813, PostgreSQL 17.12:
- Database nanou_cyber_defense: nine application tables, zero users and zero active sessions.
- Runtime role nanou_app owns the database and application tables, has CREATEROLE and CREATEDB, inherits BYPASSRLS through neon_superuser, and has broad table privileges including TRUNCATE.
- No Production snapshots or automated snapshot schedule were present; PITR history is six hours.
- Neon Free rejected Production branch protection because the protected-branch allowance was full.
- No Production schema, grants, rows, database URL, Vercel environment variables, or deployment were changed.

A least-privilege runtime-role prototype was tested only on the isolated restore-test Neon project. A NOLOGIN role passed SET ROLE, SELECT/INSERT/UPDATE/DELETE and sequence-usage smoke tests, without superuser, CREATEROLE, CREATEDB, BYPASSRLS, database/schema CREATE or TRUNCATE. The test row was deleted and zero leftovers remained. It is not a Production/Vercel login role.

PostgreSQL app startup is now schema-verify-only: it verifies required public tables and columns and does not run metadata.create_all. SQLite remains self-initializing for local development/tests. Initial PostgreSQL schema bootstrap is a separate command, python -m nanou_cyber_ai.storage.bootstrap, using protected NANOU_MIGRATION_DATABASE_URL. It is not a schema-upgrade engine; future ALTERs need explicit reviewed migrations.

## Production launch gates

Production remains BLOCKED until:
1. Create and restore a verified Production backup in an isolated destination; document RPO/RTO and rollback. No paid snapshot/upgrade without approval.
2. Create distinct migration-owner and restricted runtime login roles, test exact DDL/default grants/DML/sequences against a restored copy, then prepare a controlled cutover plan. Do not change Production ownership/grants before backup/restore proof.
3. Resolve Neon branch protection within the approved plan without weakening another service.
4. Preserve Vercel SSO; verify hosting plan, quota, monitoring, incident response and rollback.
5. Complete owner-browser Admin acceptance and separate Viewer/Analyst registration, approval, RBAC, logout and re-login checks.
6. Complete independent security review and inspect CodeQL alerts while signed in.
7. Only then consider merge to main and Production promotion, with explicit owner approval.

No Production launch, merge to main, SSO removal, paid plan upgrade, public release or real malware execution is authorized by this status document.


## 2026-11-26 verified follow-up

- Production manual snapshot prod-pre-hardening-2026-11-26 created and restored with finalize=false to isolated branch prod-restore-drill-20261126. Source and restore match across 60 public columns and all application table row counts. Production main/compute were not replaced or restarted.
- Restore-copy login-role capability and DML smoke PASS: no superuser/CREATEROLE/CREATEDB/BYPASSRLS/database CREATE/schema CREATE/TRUNCATE; SELECT/INSERT/UPDATE/DELETE and sequence privileges only; temporary probe row deleted.
- Created Production login role nanou_runtime and verified direct grants/flags. Sensitive Vercel Production NANOU_RUNTIME_DATABASE_URL now holds its connection string; legacy NANOU_DATABASE_URL unchanged. Current live Production deployment commit db4fa6a7c059467b8728468425d63ce78414ef5d does not yet read the new runtime variable, so this role is prepared but not active.
- Updated the existing sensitive Preview NANOU_RUNTIME_DATABASE_URL with the dedicated nanou_preview_runtime credential for the isolated Preview Neon project. A fresh Git Preview deployment may be required to consume the changed environment value; no deployment request or quota bypass was made.
- Production remains BLOCKED for cutover: existing nanou_app remains active and overprivileged; Neon Free does not permit protecting this default branch at current protected-branch quota; the snapshot/restore drill is not an off-provider backup or recurring schedule. Keep the existing snapshot and restore branch; no merge, Production deployment, SSO weakening or paid upgrade.
- CI baseline before these documentation-only commits: 123 passed / 4 skipped, ML smoke 13 passed, Ruff, pip-audit, Gitleaks and CodeQL PASS on prior PR #3 HEAD. New documentation commits require fresh CI/security confirmation before merge.


## Operational hardening update — 2026-11-26 (latest verified)

### Repository and deployment

- PR #1 (`feat/web-platform → main`) and PR #3 (`fix/admin-password-rotation → feat/web-platform`) remain Draft/Open, mergeable and unmerged. No Production deployment or public launch has been performed.
- PR #3 contains the current candidate. The last fully green application/test commit is `30bb422b523e1def24dcb86a16ccdc4122852d34`; documentation-only backup instructions were then added at `7721440eddfa6ae42d04b26d1653907503a1e4ee`. CI/security for the doc-only HEAD were queued at the last check.
- CI on `30bb422`: Ruff lint/format PASS; 132 passed / 4 skipped; ML smoke 13 passed; pip-audit no known vulnerabilities. Run: [45804357131](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45804357131).
- Security on `30bb422`: Gitleaks no leaks; CodeQL Python and JavaScript/TypeScript completed and SARIF upload finished. Run: [45804356605](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45804356605).
- Active GitHub ruleset `Protect main - PR and security checks` (ID `28156409`) protects `refs/heads/main`: PR required, strict required checks (`test`, `dependency-audit`, `ml-smoke`, Gitleaks and both CodeQL jobs), no non-fast-forward updates and no deletion. This is the source-repository protection path while Neon Free cannot enable another protected branch. It does not replace database backup/restore.
- Vercel Git Preview `dpl_8nmWsGxRQugKxCZFBCQT93sJrjdZ` (`720245c`) is READY at https://nanou-cyber-defense-qni7lsdw8-nanou3.vercel.app/. Live Opera checks after Preview grant correction: `/ready` returned PostgreSQL ready; `/api/auth/me` returned unauthenticated/ bootstrap already claimed; unauthenticated `/api/admin/users` correctly denied with 401. Vercel SSO remains enabled.

### Database backup and restore proof

- Production manual snapshot exists: `prod-pre-hardening-2026-11-26` (`snap-shiny-fire-bir6x6kk`) from Production branch `main`.
- Isolated restore branch: `prod-restore-drill-20261126` (`br-little-sound-bipv6bjm`). Source/restore comparison showed 9 application tables and 60 columns; row-count comparison matched at snapshot time.
- The restore branch was used to validate NOLOGIN ownership transfer, separate migration login, future default grants and runtime DML after ownership transfer. The test branch was modified for the drill; Production `main` was not.
- New encrypted backup tools use RSA-3072 OAEP-SHA256 + AES-256-GCM, authenticated decryption and bounded streaming. Public key: `backups/production-backup-public.pem`; private key remains local on Termux with mode 600 and is not in Git.
- `.github/workflows/production-backup.yml` is staged, but scheduled backup is **BLOCKED / NOT ACTIVE** until Actions secret `NANOU_BACKUP_DATABASE_URL` is provisioned. No cleartext dump was uploaded; no automated backup artifact or automated restore has yet been proven. See `docs/production-backup-restore.md`.

### Production Neon roles

Production Neon project `cold-resonance-28231813`, default branch `main`, database `nanou_cyber_defense`:

- `nanou_runtime`: login role tested against all 9 tables / 60 columns. SELECT/INSERT/UPDATE/DELETE and sequence access work. No SUPERUSER, CREATEROLE, CREATEDB, BYPASSRLS, database CREATE, schema CREATE or TRUNCATE. Disposable DML probe was deleted; zero leftovers.
- `nanou_backup`: login role with SELECT only on all 9 tables and SELECT on both sequences; INSERT/UPDATE/DELETE/TRUNCATE/CREATE are not granted. Current snapshot data was readable (0 users, 2 audit events, 0 auth sessions).
- `nanou_migration_owner`: NOLOGIN; no SUPERUSER/CREATEROLE/CREATEDB/BYPASSRLS. Has the public-schema CREATE privilege required for controlled schema ownership/migrations. Default privileges are prepared: runtime receives table DML and sequence usage; backup receives SELECT only.
- `nanou_migration_login`: separate login with no SUPERUSER/CREATEROLE/CREATEDB/BYPASSRLS and no direct public-schema CREATE. Its membership permits `SET ROLE nanou_migration_owner` only when performing reviewed migrations. A create/drop table smoke test passed under that role.
- Legacy `nanou_app` still owns the Production database and current tables at this staged point. The new owner role and grants are prepared but ownership has **not** yet been transferred on Production. Do not delete or revoke the legacy role until the new runtime candidate is deployed, verified, and the rollback window is closed.
- Vercel Production environment now has a separate `NANOU_RUNTIME_DATABASE_URL` for `nanou_runtime` and a separate `NANOU_AUDIT_HMAC_KEY`; the old `NANOU_DATABASE_URL` remains unchanged for the transition/rollback. Secret values are never printed. Production has not yet been redeployed against the new runtime role.

### Remaining launch gates

1. Provision the GitHub Actions secret `NANOU_BACKUP_DATABASE_URL` from the read-only `nanou_backup` role through a supported secure secret-setting route; then run the backup workflow, download/decrypt/restore its artifact in an isolated branch, and record checksum/RPO/RTO.
2. Complete PR #3 → PR #1 and PR #1 → main only after exact-head CI/security passes and owner merge approval; then verify Production deployment uses `NANOU_RUNTIME_DATABASE_URL`.
3. After Production smoke passes and rollback is proven, transfer Production database/tables/sequences to `nanou_migration_owner`, verify default grants, and retire the old `nanou_app` role/credential only when no longer required.
4. Production user count remains zero and `bootstrap_claimed=false`; create/verify the owner Admin through the approved secure bootstrap path before public use. Do not invent or disclose passwords.
5. Complete owner Admin, Viewer and Analyst RBAC acceptance; keep SSO on; review monitoring, incident response, CodeQL alerts and hosting quotas.

No data was migrated or deleted on Production; no Production ownership transfer, merge to `main`, Production promotion, SSO removal, paid upgrade or live public launch occurred in this update.

## Latest continuation — 2026-11-26 (supersedes earlier status above)

### Source integration

- PR #1 is merged to `main`; merge commit `53ba75d554df28a219a3821254ed7226367bfe24`.
- PR #10 (purpose-separated HMAC fingerprints, hosted fail-closed) is merged to `main`; merge commit / current `main` HEAD `fe47b815fa90bd2bacd06d4ab4e139e874fce88b`.
- CI and Security on PR #10 exact head `67365e58290187bbcf5a00e936355418046b9dac` passed: Ruff/tests, ML smoke, dependency audit, Gitleaks, CodeQL Python and JavaScript/TypeScript. The merge commit has the same tree as that checked PR head.
- PR #3 (password rotation + PostgreSQL schema verification) and PR #4 (backup workflow secret scoping) remain Draft/Open and unmerged. A clean temporary integration clone was created; the original Termux checkout remains untouched at `f2427a2332c22488f1a819fa177f5a105a0dcfe4` with its pre-existing dirty tests.
- The integration branch combines main with PR #3 password rotation and PostgreSQL schema verify-only startup. PR #4's alternative backup workflow was not adopted: comparison showed it removed the existing read-only-role/privilege and RLS preflight checks. Main's stronger step-scoped backup workflow was retained. Six conflicts were resolved in the temporary clone; targeted tests and exact-head CI/security are still required before opening a review PR. No Production merge is authorized by this preparation.

### HMAC and runtime configuration

- `NANOU_AUDIT_HMAC_KEY` exists as a Vercel sensitive Production environment variable; its value was not read. Main now uses keyed HMAC-SHA256 for audit/rate-limit fingerprints (PR #10). The integration candidate keeps purpose separation and fails closed on Vercel/AWS Lambda when the dedicated key is missing.
- Production `NANOU_RUNTIME_DATABASE_URL` exists as a sensitive environment variable and selects the restricted `nanou_runtime` role. The legacy `NANOU_DATABASE_URL` remains for rollback. No values were decrypted or printed.
- PostgreSQL startup in the candidate verifies the expected tables/columns and performs no DDL; schema bootstrap remains a separate reviewed migration-owner operation.

### Backup and restore evidence

- GitHub Actions secret name `NANOU_BACKUP_DATABASE_URL` is present (name only checked; value not read). The main-branch Production backup workflow is active and two manual runs succeeded: `45850155507` and `45852927966`.
- Artifact from run `45852927966`: `nanou-production-20261126T155020Z.ncdb`; SHA-256 `7d10aa52c03d4fe03b00244a37c539bf019a79992271b476f27c19f4da308f81`. Sidecar checksum PASS.
- Authenticated decryption and `pg_restore --list` PASS. A local isolated PostgreSQL 18.2 restore on Termux PASS: 9 tables, 60 columns; users=0, audit_events=2, auth_attempts=4, auth_sessions=0, platform_state=1. The temporary cluster was stopped and removed after verification. Production was not touched.
- This verifies encrypted-artifact decrypt/restore to local PostgreSQL. A separate Neon branch restore of this exact artifact and a second offline recovery copy of the private key remain outstanding. The private key stays local with mode 600.

### Production deployment and cutover

- Latest Vercel Production deployment remains READY on old commit `46afde6042841715364f416623a416022a8476d1`; it has not yet deployed the current `main` runtime selector/HMAC code.
- Attempted exact-HEAD Production deployment of `fe47b815fa90bd2bacd06d4ab4e139e874fce88b` was rejected with Vercel HTTP 402 `api-deployments-free-per-day` (more than 100 deployments/24h; retry-after 86400 seconds). Vercel CLI was not installed/authenticated on the Nanou Termux device; no CLI bypass, plan upgrade or quota change was attempted.
- Production `nanou_runtime`, `nanou_backup`, `nanou_migration_owner` (NOLOGIN), and `nanou_migration_login` are staged. `nanou_app` still owns the Production database/tables and has elevated privileges. Do not transfer ownership or revoke legacy credentials before a tested runtime deployment and rollback window.
- GitHub main ruleset `28156409` protects source with PR/strict checks. Neon Production branch protection remains constrained by the Free-plan protected-branch quota.
- Production user count remains zero and bootstrap is not claimed. Owner Admin bootstrap plus live Viewer/Analyst registration, approval, RBAC and logout/re-login acceptance are still required. Keep Vercel SSO enabled.

No Production ownership transfer, migration, credential retirement, new Production deployment, SSO removal, paid upgrade or public launch occurred in this continuation.
