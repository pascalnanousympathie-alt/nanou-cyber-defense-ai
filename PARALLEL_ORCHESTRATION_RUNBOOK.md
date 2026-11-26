# Parallel Orchestration Runbook — Nanou Cyber Defense AI

Last verified: 2026-11-26 (UTC)

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
- `nanou_migration_login`: separate login; no direct schema CREATE or elevated role attributes; membership grants SET ROLE to migration owner for reviewed DDL. Create/drop table smoke test passed.
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


## 12. Latest continuation evidence and PR #4 dependency

- PR #3 latest validated SHA at this checkpoint: `7d10fb6666515d5bf6816710566f5d276d0402dc`.
- Security workflow PR-base filters now include `fix/admin-password-rotation`, so Gitleaks and both CodeQL languages run for child pull requests targeting PR #3.
- PR #3 exact-head CI #45819559656: Ruff, 132 passed / 4 skipped, ML smoke 13, dependency audit PASS. Security #45819559546: Gitleaks and both CodeQL jobs PASS.
- PR #4 `fix/backup-runner-secret-scope` → `fix/admin-password-rotation`, exact head `7e002e5e165da84779dba819d6e5f11abbb8aba2`: CI #45817693674 PASS (132/4, ML 13, pip-audit); exact Vercel Preview deployment dpl_M8BsQApGiBKFCw23w3okDAh91znA READY. Verify Gitleaks/CodeQL on PR #4 exact head before merge; the earlier scan results belong to PR #3 head, not PR #4.
- PR #4 modifies only `.github/workflows/production-backup.yml`. The DB URI is parsed in the dump step and passed to libpq via environment variables, not command-line arguments. TLS is mandatory; unsupported query options fail closed; temporary connection file is 0600; dump directory 0700; dump uses umask 077 and the runner UID.
- Production runtime and backup login checks passed for direct read queries. Preview runtime login also passed. A separate isolated restore-test role completed INSERT → UPDATE → DELETE smoke with no residual test row.
- The Production snapshot/restore evidence remains the manual snapshot `snap-shiny-fire-bir6x6kk` and branch `br-little-sound-bipv6bjm`; no automatic/off-provider backup has been proven.
- `NANOU_BACKUP_DATABASE_URL` is still required as a GitHub Actions secret. The available GitHub connector cannot write repository Actions secrets. Owner must provision this secret through GitHub's secret settings using the read-only `nanou_backup` connection; never paste the secret into chat, Git, shell history or logs.
- Production remains on old deployment commit `db4fa6a7c059467b8728468425d63ce78414ef5d`; old `nanou_app` still owns database/tables. No ownership transfer or credential revocation until exact Production runtime deployment and backup/restore/rollback acceptance.
- Keep all PRs Draft/Open and do not merge, promote, disable SSO, or upgrade until the required human acceptance and backup secret handoff are complete. No direct Production DDL or data writes during this checkpoint.
