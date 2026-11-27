# Parallel Orchestration Runbook — Nanou Cyber Defense AI

Last verified: 2026-11-27 (UTC)

## Latest verified continuation — 2026-11-27 (after Signify security fix)

This addendum supersedes older main-commit, PR #14, deployment, and browser-session status statements below.

- PR #14 (`fix(security): patch Signify dependency and EMBER compatibility`) is **MERGED** into `main` as `93c6c67af35251889c94975814e8d7edadbc44ae`. Main now declares `ember-extract = ["signify==0.9.3"]`; the EMBER2024 compatibility patch and regression tests are included.
- Exact merge-candidate CI run [45985042915](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45985042915) passed: Ruff lint/format, **155 passed / 4 skipped**, ML smoke **13 passed** with `EMBER_SIGNIFY_COMPAT_PASS`, and dependency audit **No known vulnerabilities found**.
- Exact merge-candidate Security run [45985042891](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45985042891) passed: Gitleaks, CodeQL Python, and CodeQL JavaScript/TypeScript.
- Main push CI [45985294426](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45985294426) and Security [45985295324](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45985295324) also completed with all jobs successful on merge commit `93c6c67`.
- Vercel Production deployment `dpl_CuAyxdFkCHFCjMbw4XtctPMs1WgP` is **READY** on that exact main commit. Authenticated Opera smoke checks after alias assignment returned `/health` HTTP 200, `/ready` HTTP 200 with PostgreSQL, and `/api/auth/me` authenticated as active Admin. Vercel SSO remains enabled.
- The previous pre-merge Dependabot inventory showed one OPEN HIGH Signify alert (`GHSA-p4hh-mq57-gq8x`, affected versions below 0.9.2). After the merge, the connected GitHub alert-list endpoint was not available, so the alert's current state is **NOT VERIFIED**; do not claim that GitHub has closed it until the dependency graph/alert page is checked. The source pin is fixed and both dependency-audit runs reported no known vulnerabilities.
- Production backup scheduling remains **NOT VERIFIED**: cron is `43 2 * * *` UTC; the next expected event is 2026-11-28 02:43 UTC. Require a real `schedule` event and encrypted artifact before marking it PASS.
- The independent offline second copy of the backup private key remains **NOT VERIFIED**; no separate removable/offline destination was mounted. The primary local key remains mode 600.
- The owner Opera Admin session is currently authenticated and verified. Only one Admin account is present; separate Viewer/Analyst live RBAC acceptance remains pending.
- The read-only Opera-to-Termux Admin bridge was verified in this session: `ping`, `whoami`, `users`, and `audit` passed; local directory/socket permissions are 0700/0600. The bridge remains session-bound and requires Opera to stay open and signed in.


## Current verified Production state — 2026-11-27

This live-state addendum supersedes older staged-state notes later in this file.

- Repository visibility is public. PR #13 is merged; `main` is at `cdeae3e34937a8e687585725b3d09b58bafa2eec`. Backup workflow remains active with UTC cron `43 2 * * *`. Verify the first scheduled event at 2026-11-28 02:43 UTC; do not mark schedule delivery PASS before a real `schedule` run and encrypted artifact are observed.
- Vercel Production deployment `dpl_2gn4F1XNZazuevbDnbfAApW5xb1X` is READY on that commit; canonical `/ready` returns HTTP 200 with PostgreSQL ready.
- Production ownership transfer is **APPLIED and directly verified** on Neon main (`br-damp-fog-bi0lzjf4`): `nanou_migration_owner` owns the database, all 9 application tables and both sequences (11 objects). `nanou_app` owns none of these objects but retains elevated role attributes/memberships; preserve it until a separate rollback and credential-retirement plan is reviewed. Fresh direct SQL queries succeeded with explicitly selected DB roles.
- Post-cutover privilege checks: `nanou_runtime` has SELECT/INSERT/UPDATE/DELETE on all 9 tables, no TRUNCATE/TRIGGER/REFERENCES, SELECT/USAGE (not UPDATE) on both sequences, and no database/schema CREATE. `nanou_backup` has SELECT-only on all 9 tables and sequence SELECT (not USAGE/UPDATE). `nanou_migration_login` successfully performs `SET LOCAL ROLE nanou_migration_owner` in a READ ONLY transaction; the effective owner is NOLOGIN and non-elevated.
- The separate `prod-role-transfer-rehearsal-20261126` branch (`br-morning-art-bi0ubfr1`) remains distinct from Production and still has `nanou_app` as database owner while `nanou_migration_owner` owns its tables/sequences. Do not confuse this rehearsal branch with the completed Production cutover.
- Legacy `nanou_app` remains login-enabled and retains CREATEROLE/CREATEDB/REPLICATION/BYPASSRLS and memberships including `neon_superuser`, but owns zero current Production database/tables/sequences. Do not revoke or disable it until the rollback and credential-retirement plan is reviewed.
- Dependabot vulnerability alerts are enabled. Current inventory: 1 OPEN HIGH `signify` alert (`GHSA-p4hh-mq57-gq8x`, vulnerable `<0.9.2`); 0 dismissed/fixed/auto-dismissed. PR #14 upgrades to `signify==0.9.3`; CI, ML smoke, dependency audit and Security pass on head `9ce497a`. The alert remains OPEN until merge and GitHub dependency-graph refresh.
- Owner browser Admin acceptance and Viewer/Analyst live RBAC acceptance are pending because the inspected Opera app profile is signed out. Never enter or request credentials or bootstrap token in chat.
- Private backup key is on Termux with mode 600. Independent offline second copy remains NOT VERIFIED until a separate removable/offline destination is mounted and checked.
- Manual backup run `45946937978` completed SUCCESS and produced a 23,362-byte artifact; this verifies workflow/artifact creation, not Production ownership transfer or restore of this particular artifact. Separate run `45941044613` has a verified checksum, authenticated decrypt, archive listing and full isolated local PostgreSQL restore with all 9 table row counts matching Production. No scheduled event has yet been observed after PR #13; first expected validation is 2026-11-28 02:43 UTC.


## 1. Repository boundaries

Repository: pascalnanousympathie-alt/nanou-cyber-defense-ai.

Do not mix this repository with LudoMada, Nanou Browser, Mada Commander, PC-Free, Rami, Loto or Domino projects. Do not infer a deployment, database or credential from another project.

## 2. Source of truth and start-of-task checks

Before any work:
1. Read PROJECT_STATUS.md, this runbook and docs/deployment.md.
2. Read current PR #1 and PR #3 heads/bases, commit history, CI/security runs, and Vercel deployment metadata.
3. Check branch compare (ahead/behind), mergeability and changed files.
4. Inspect exact files/anchors before edits. Prefer small, sequential commits on the intended branch.
5. If status/runbook files are absent in a future branch, do not invent their contents; find the latest docs/PR evidence and recreate them only if needed.

Do not assume previous chat status is still current. Use current GitHub/Vercel/Neon evidence.

## 3. Branch and PR topology

- PR #1: feat/web-platform → main.
- PR #3: fix/admin-password-rotation → feat/web-platform.
- PR #3 depends on PR #1. Keep PR #3 based on the latest PR #1 branch.
- Current state: both Draft/Open, mergeable, unmerged. PR #3 head at last verification: 590488b8afebfa740add47dbd8757588c8033634; base 62f0b42bcec2a096186a84e18029048f3ce320da.
- A normal merge commit was used to synchronize PR #3 to PR #1; no rebase or force-push.

Never merge PR #3 to PR #1 or PR #1 to main without explicit owner approval. Never mark a PR ready or close it unless its acceptance gates are met and owner intent is clear.

## 4. Safe parallel work

Parallelize only independent areas:
- UI/CSS/menu and documentation can proceed separately from database-role design.
- Authentication/RBAC changes must be serialized against shared auth/storage files.
- Database schema/bootstrap/runtime-role work must be coordinated as one stream; do not run concurrent schema changes.
- CI/security workflow files are shared gates; avoid duplicate workflow definitions and unnecessary reruns.
- After any remote file edit, refetch the branch file and verify SHA/content before the next edit.

No force-push, reset, clean, stash, rebase or pull-over-dirty operations. Use a fresh isolated temporary clone for local checks. Keep the user's existing Termux checkout and dirty files untouched. Confirm clean status in the isolated clone before push.

## 5. Required validation

For Python or UI changes, require:
- Ruff lint and format.
- Full pytest suite.
- ML smoke tests (EMBER/LAMDA).
- pip-audit.
- Gitleaks full-history/refs scan.
- CodeQL Python and JavaScript/TypeScript.

Read logs and identify the first failing step. A failed lint gate means pytest skipped; do not call that a test failure. runner_id=0 or empty steps indicates a run that did not start and is not a root cause by itself.

Current verified baseline: CI #45794790570 passed 123 tests / 4 skipped, 13 ML smoke tests, and pip-audit. Security #45794790508 passed Gitleaks and both CodeQL uploads.

## 6. Preview and Vercel rules

- Vercel project: nanou-cyber-defense-ai, team slug nanou3.
- Keep Vercel Authentication/SSO enabled for all deployments.
- Current READY branch Preview: https://nanou-cyber-defense-ai-git-fix-admin-password-rotation-nanou3.vercel.app/, deployment dpl_HSoSTJv8aFcudRrLBtJw7XskY2PW, commit ad2f668c8323996a16366ade5b4f69f652f8d9e4.
- This Preview app code matches current PR #3 runtime/UI source; it is 11 commits behind on docs/tests and small bootstrap CLI error handling only.
- Latest live checks: PostgreSQL /ready PASS; signed-out /api/auth/me; unauthenticated Admin users request denied.
- Manual Vercel API deployment hit the Free daily limit (api-deployments-free-per-day, >100, retry-after 24h). Do not bypass with CLI, reuse guessed aliases, make repeated deployment attempts, disable SSO or buy an upgrade. Use Git-linked Preview once quota permits; verify exact commit SHA.

## 7. Neon / database separation

- Preview and Production Neon projects and Vercel database credentials must remain distinct.
- Never print database URLs, passwords, HMAC keys, session tokens, API keys or bootstrap tokens.
- Production runtime role nanou_app is currently over-privileged and owns the database/tables. Production has no verified backup/snapshot schedule and branch protection is blocked by the Neon Free limit.
- Runtime code must not run PostgreSQL DDL. It now verifies tables/columns; SQLite auto-creation remains local-only.
- Initial PostgreSQL schema setup uses a separate migration connection via NANOU_MIGRATION_DATABASE_URL; future changes require reviewed migrations.
- A NOLOGIN DML-only prototype passed only in the isolated restore-test project. Do not reuse it as a Production credential.
- Never change Production ownership, grants, connection strings, schema or data before a successful Production backup/restore drill and explicit owner approval.

## 8. Product security boundary

Keep this product defensive:
- No malware execution, binary/APK upload/launch, shell/process runner, exploit automation, arbitrary target scanning or autonomous remediation.
- Tabletop simulation is deterministic/local reporting only, not network exploitation.
- Malware feature preparation validates pre-extracted one-row CSV; it is not direct APK scanning.
- External AI provider is not enabled without a securely configured server-side key and approved service-to-service access model.
- A trusted SHA-256-verified model artifact and separately validated threshold are required before claiming malware inference readiness.

## 9. Escalation / blockers

Use this status format:
- BLOCKED — exact evidence, resource/action required, safe independent work that can continue.
- PASS — commit/run/deployment ID and relevant test/log evidence.
- NOT VERIFIED — no direct proof yet; do not claim success.
- Do not re-report resolved issues (e.g. GitHub Actions billing) without new evidence.
- Do not confuse a signed-out browser's expected 401 with a broken RBAC gate.
- Do not claim zero CodeQL alerts unless the authenticated Security dashboard has been inspected.

## 10. Production go-live checklist

Production is blocked until:
- Backup/restore and rollback proven from Production data.
- Least-privilege migration/runtime role design tested on a restored copy and cutover plan reviewed.
- Neon branch protection and Vercel deployment protection resolved within approved plan/quota.
- Owner Admin and separate Viewer/Analyst acceptance complete.
- Monitoring, alert response, incident plan, retention and hosting-plan suitability reviewed.
- CI/security green on the exact merge candidate.
- Owner explicitly approves merge to main and Production promotion.


## 11. 2026-11-26 restore drill and role preparation

- Production snapshot prod-pre-hardening-2026-11-26 was restored with finalize=false into br-little-sound-bipv6bjm (prod-restore-drill-20261126). Source and restored branch match across 60 public columns and application row counts. Do not finalize or swap this branch into main; it is a retained restore-test copy.
- A login role on the restored copy passed capability checks and INSERT/UPDATE/DELETE smoke. It lacks superuser, CREATEROLE, CREATEDB, BYPASSRLS, database/schema CREATE and TRUNCATE, and has DML plus sequence USAGE/SELECT. Probe row count after test was zero.
- Production login role nanou_runtime was created and verified with equivalent least-privilege flags/grants. Its connection string is held in Vercel sensitive Production NANOU_RUNTIME_DATABASE_URL. Existing NANOU_DATABASE_URL and live nanou_app remain untouched. Current Production deployment code (db4fa6a7c059467b8728468425d63ce78414ef5d) does not consume the runtime variable; role is staged only.
- Vercel Preview NANOU_RUNTIME_DATABASE_URL is set to the dedicated nanou_preview_runtime credential on the separate Preview Neon project. Existing deployment may need a fresh Git-linked Preview to consume it. Do not bypass deployment quotas.
- Do not finalize the restore branch, change Production ownership/grants, revoke nanou_app, deploy, merge, disable SSO, or buy upgrades without explicit approval and a tested rollback. The manual snapshot is not offsite backup or recurring automation; Neon Free protection quota remains unresolved.
- After the documentation commit, rerun full CI/security on exact PR #3 HEAD; the prior green run is only a baseline, not evidence for the new HEAD.


## 11. Latest Production role, backup and Preview evidence (2026-11-26)

### Current verified branch/CI state

- PR #3 remains Draft/Open and unmerged to PR #1; PR #1 remains Draft/Open and unmerged to `main`.
- Latest fully green application/test HEAD: `30bb422b523e1def24dcb86a16ccdc4122852d34`.
- CI #45804357131: 132 passed / 4 skipped; Ruff lint/format, ML smoke 13, dependency audit all PASS.
- Security #45804356605: Gitleaks no leaks; CodeQL Python and JavaScript/TypeScript completed and SARIF uploads finished.
- Docs-only commits were added after `30bb422`; do not claim those exact later SHAs green until their own runs complete.
- GitHub main ruleset ID `28156409` is active and requires a PR, strict test/dependency-audit/ML/Gitleaks/CodeQL status checks, blocks non-fast-forward updates and deletion. Neon Free branch-protection quota is therefore not a blocker for source control. This is not database protection.

### Backup/restore

- Production manual snapshot: `snap-shiny-fire-bir6x6kk`, name `prod-pre-hardening-2026-11-26`.
- Isolated restore drill branch: `br-little-sound-bipv6bjm`, name `prod-restore-drill-20261126`.
- Source and restored schema/column checks matched (9 application tables / 60 columns) and row counts matched at snapshot time.
- The restore branch was further used to prove no-login ownership and migration-role semantics. It is a drill copy, not Production.
- Encrypted backup implementation is in `src/nanou_cyber_ai/backup/crypto.py`; RSA-3072 OAEP-SHA256 wraps a random AES-256-GCM key, data streams in 1 MiB chunks and authenticated decryption removes untrusted partial output.
- The private recipient key remains local at `~/.local/share/nanou-cyber-defense-ai/backup-keys/production-backup-private.pem` with mode 600. Never commit or print it.
- Scheduled workflow `.github/workflows/production-backup.yml` needs GitHub Actions secret `NANOU_BACKUP_DATABASE_URL`. This secret has not been provisioned; the workflow is committed but NOT ACTIVE. No automated encrypted artifact/restore proof exists yet.

### Production roles staged

- `nanou_runtime`: login role tested on Production branch, can SELECT/INSERT/UPDATE/DELETE and use sequences; cannot CREATE/TRUNCATE, CREATEROLE, CREATEDB, BYPASSRLS or bypass RLS.
- `nanou_backup`: read-only login; SELECT on all nine tables and sequence state; no DML or TRUNCATE.
- `nanou_migration_owner`: NOLOGIN, no CREATEROLE/CREATEDB/BYPASSRLS, public schema CREATE capability and default grants prepared for runtime DML + backup SELECT.
- `nanou_migration_login`: login role with no elevated flags and no direct schema CREATE. Read-only Production test on 2026-11-27 successfully executed `SET LOCAL ROLE nanou_migration_owner`; no DDL was run, so this does not prove a create/drop migration smoke test.
- Production database and current tables remain owned by `nanou_app` until deployment cutover. Do not transfer ownership or delete legacy role before current Production app has switched to `NANOU_RUNTIME_DATABASE_URL` and rollback is verified.
- Vercel Production has staged `NANOU_RUNTIME_DATABASE_URL` and a distinct `NANOU_AUDIT_HMAC_KEY`; legacy `NANOU_DATABASE_URL` is unchanged. Secret values must not be displayed.
- Preview uses its own Neon project and `nanou_preview_runtime`. After grants were applied by the existing table owner, Preview /ready returned PostgreSQL ready, auth/me was signed out with bootstrap already claimed, and unauthenticated Admin endpoint correctly returned 401.

### Production promotion order

1. Provision `NANOU_BACKUP_DATABASE_URL` through a supported secret-management route and run scheduled/manual backup; decrypt and restore it on an isolated target, verify checksum/schema/rows.
2. Ensure exact candidate CI/security are green.
3. Merge PR #3 into PR #1 and PR #1 to main only with explicit owner approval and ruleset checks.
4. Confirm Vercel Production runs the new code, uses `nanou_runtime`, /ready passes, auth routes work and Admin routes remain protected.
5. Transfer DB/tables/sequences to `nanou_migration_owner` only after step 4; preserve a reviewed rollback window.
6. Retire `nanou_app` credentials only after backup/restore, new runtime and rollback acceptance.
7. Bootstrap Production Admin through the secure path; do not send passwords in chat.
8. Complete Viewer/Analyst RBAC and operational acceptance.

Never bypass the stopped secret handoff by embedding credentials in shell history, command arguments, repository files, logs or chat. If the supported secret write action remains unavailable, report BLOCKED with the exact missing secret and continue independent work.

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
- This verifies encrypted-artifact decrypt/restore to local PostgreSQL. A Neon branch restore of this exact artifact now PASSes on `br-little-sound-bipv6bjm` (`prod-restore-drill-20261126`), database `nanou_restore_drill_20261126`, using the isolated `nanou_runtime_restore_probe` role. The Production main branch row counts were queried read-only afterward and remained identical (users=0, audit_events=2, auth_attempts=4, auth_sessions=0, platform_state=1). A second offline recovery copy of the private key remains outstanding. The private key stays local with mode 600.

### Production deployment and cutover

- Latest Vercel Production deployment remains READY on old commit `46afde6042841715364f416623a416022a8476d1`; it has not yet deployed the current `main` runtime selector/HMAC code.
- Attempted exact-HEAD Production deployment of `fe47b815fa90bd2bacd06d4ab4e139e874fce88b` was rejected with Vercel HTTP 402 `api-deployments-free-per-day` (more than 100 deployments/24h; retry-after 86400 seconds). Vercel CLI was not installed/authenticated on the Nanou Termux device; no CLI bypass, plan upgrade or quota change was attempted.
- Production `nanou_runtime`, `nanou_backup`, `nanou_migration_owner` (NOLOGIN), and `nanou_migration_login` are staged. `nanou_app` still owns the Production database/tables and has elevated privileges. Do not transfer ownership or revoke legacy credentials before a tested runtime deployment and rollback window.
- GitHub main ruleset `28156409` protects source with PR/strict checks. Neon Production branch protection remains constrained by the Free-plan protected-branch quota.
- Production user count remains zero and bootstrap is not claimed. Owner Admin bootstrap plus live Viewer/Analyst registration, approval, RBAC and logout/re-login acceptance are still required. Keep Vercel SSO enabled.

No Production ownership transfer, migration, credential retirement, new Production deployment, SSO removal, paid upgrade or public launch occurred in this continuation.

## Current Production checkpoint — 2026-11-27

The earlier historical statements in this runbook that Production had zero users and bootstrap was unclaimed are superseded by this checkpoint.

- GitHub main is exactly a6e15da951641f2f6983c01afc8f8b0484fd3f31. PR #11 is merged; CI 45889588789 and Security 45889588961 completed successfully on the production source.
- Vercel Production deployment dpl_2AxU3iCjEYUWkJRp4iSDrCwbWSur is READY on commit a6e15da. /health and /ready both returned HTTP 200; /ready identified PostgreSQL. Vercel SSO remains enabled.
- Production Neon platform_state.bootstrap_claimed=true; there is exactly one active, approved Admin, one unexpired auth session, and one successful auth.bootstrap audit event. NANOU_BOOTSTRAP_TOKEN is a sensitive Production-only variable; no secret value was read.
- nanou_runtime has least-privilege DML and sequence access; it has no TRUNCATE, schema CREATE or elevated role attributes. nanou_app remains the public-table owner and retains elevated flags/membership (neon_superuser, nanou_migration_owner). No Production ownership/grant/credential cutover was performed.
- Opera Connector's current profile is signed out of the app (/api/auth/me: authenticated=false, bootstrap_required=false). The Admin API's 401 from that profile is expected. Do not interpret it as a broken Admin bootstrap.
- Live Viewer/Analyst registration and approval, role-specific acceptance, owner-browser logout/re-login and password-change acceptance are still outstanding. Production must not be declared unrestricted-public-launch ready yet.
- Encrypted backup/restore evidence remains the previously verified 2026-11-26 run history; the second offline private-key recovery copy is still NOT VERIFIED. Do not print or upload the private key.
- Next safe sequence: complete account acceptance with identities controlled by the owner; verify alerting/monitoring and the backup recovery copy; prepare the database ownership cutover/rollback checklist. Production ownership transfer, legacy-role retirement or permission changes require explicit approval and a tested rollback window.


## Runtime-role and backup-scheduler follow-up — 2026-11-27 (latest)

- Re-read `src/nanou_cyber_ai/settings.py` from `main` at Production commit `a6e15da951641f2f6983c01afc8f8b0484fd3f31`: `effective_database_url` selects `NANOU_RUNTIME_DATABASE_URL` first and returns no database URL on Vercel/AWS Lambda if that dedicated value is missing; it does not fall back to the legacy owner credential on hosted runtimes.
- Vercel environment-variable metadata (decrypt=false) confirms sensitive Production `NANOU_RUNTIME_DATABASE_URL` and `NANOU_AUDIT_HMAC_KEY` entries exist. No secret values were decrypted or read.
- Live Opera GET `/ready` returned `{"status":"ready","database":"postgresql"}`. A read-only Production `pg_stat_activity` query immediately afterward observed one idle `nanou_runtime` connection through PgBouncer. The `nanou_app` active connection in that query was the owner-role inspection connection itself. This supplies direct evidence that the deployed application exercised the restricted runtime login.
- A fresh role-catalog check confirms `nanou_runtime` has no SUPERUSER, CREATEROLE, CREATEDB, REPLICATION or BYPASSRLS; it is not a member of `neon_superuser` or `nanou_migration_owner`. `nanou_backup` is similarly unprivileged. `nanou_app` remains login-enabled, has CREATEROLE/CREATEDB/REPLICATION/BYPASSRLS and remains a member of `neon_superuser` and `nanou_migration_owner`.
- No Production database ownership, grants, credentials, or deployment settings were changed. The staged runtime-role cutover therefore remains incomplete: keep `nanou_app` intact until the owner approves a reviewed cutover/rollback plan and the complete schema-owner/default-grant sequence is tested.
- The backup workflow still declares a daily `17 2 * * *` UTC schedule plus manual dispatch. GitHub Actions main-branch run history as of 2026-11-27T04:34Z shows the latest Production backups remain the two successful manual `workflow_dispatch` runs `45850155507` and `45852927966` from 2026-11-26; no scheduled backup run is visible after the 2026-11-27 02:17 UTC schedule time. This does not prove the workflow is disabled, only that a scheduled execution is not evidenced. Do not claim schedule PASS until a scheduled run and encrypted artifact are confirmed.
- Vercel Production remains READY on `a6e15da`; runtime errors were not observed in the last 24 hours. PR #12 remains documentation-only, open, mergeable and unmerged.


## Full backup restore and scheduled-trigger diagnosis — 2026-11-27

- Manual encrypted backup run `45941044613` completed successfully on main `a6e15da`; artifact `nanou-production-backup-45941044613` (ID `15172521803`) is retained until 2026-12-27. GitHub ZIP digest: `be57978e1000edbc00a35111eef4ed23b89e69664ac62f617222a6fe36612380`. Encrypted payload sidecar checksum: PASS.
- Authenticated decryption, archive listing and a complete restore into a separate disposable PostgreSQL cluster passed. Row counts matched a direct read-only Production count query over all 9 public application tables: api_keys 0; attack_scopes 0; attack_simulations 0; audit_events 3; auth_attempts 2; auth_sessions 1; malware_metadata 0; platform_state 1; users 1.
- First local restore invocation encountered an already-existing `public` schema in PostgreSQL's newly created template database. This was a disposable-target invocation issue, not archive corruption: rerun with `--clean --if-exists` succeeded. The temporary cluster used port 55440, was stopped and deleted; the pre-existing Termux PostgreSQL service on port 5432 remained online and unchanged. Production was never used as a restore target.
- GitHub CLI currently lists the backup workflow as `active`; `main` is the repository default branch and holds the workflow file; the workflow's last cron-file commit was on 2026-11-26 by the same account currently authenticated with GitHub CLI. The scheduled run history still contains zero `schedule` events for the expected 2026-11-27 execution, although manual `workflow_dispatch` succeeds.
- GitHub's documented candidate explanations are schedule queue delay/drop during Actions load, or a stopped schedule associated with an actor that was suspended/deprovisioned even while manual dispatch works. Repository activity is recent, so the public-repository 60-day inactivity safeguard is not a supported explanation here. Historical schedule-actor state cannot be proven from the connected interface. See [GitHub troubleshooting](https://docs.github.com/en/actions/how-tos/troubleshoot-workflows).
- The cron line currently remains `17 2 * * *` UTC on `main`. No main-branch cron change was made in this update. A separate PR is being prepared to shift the minute and resynchronize the schedule; it must be merged to `main` by an authorized owner before its new schedule can take effect.
- The private recovery key remains only on the authorized Termux device (mode 600). No second offline copy or removable storage destination was found in the scoped shared-storage inventory. The internal shared-storage area is not an acceptable substitute for an offline recovery copy.
- Code Scanning reports 0 open alerts; Dependabot alert visibility is BLOCKED by GitHub permission scope. Do not claim a clean Dependabot inventory.


## Production migration-role state — 2026-11-27

- Verified read-only: `nanou_migration_login` can `SET LOCAL ROLE nanou_migration_owner`; effective owner role is NOLOGIN and non-elevated, with public-schema USAGE/CREATE.
- Verified read-only: owner-role default ACLs grant future table DML to `nanou_runtime`, table SELECT to `nanou_backup`, sequence SELECT/USAGE to runtime, and sequence SELECT to backup.
- Verified read-only: runtime grants cover all 9 Production tables and 2 sequences without TRUNCATE/TRIGGER/REFERENCES; backup is SELECT-only for tables.
- Current ownership is unchanged: `nanou_app` still owns the Production database and all 9 public tables. No Production ownership/grant/credential changes were made.
- Correction: the retained `prod-restore-drill-20261126` copy currently has a runtime restore probe as DB/table owner and no default ACL rows; do not cite that copy as current proof of full migration-owner ownership transfer. The separate `nanou-cyber-defense-restore-drill` project is a runtime-grant prototype, not a Production cutover rehearsal.
