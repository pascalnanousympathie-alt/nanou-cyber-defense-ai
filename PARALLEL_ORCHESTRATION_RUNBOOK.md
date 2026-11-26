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
