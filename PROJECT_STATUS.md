# Project Status — Nanou Cyber Defense AI

Last verified: 2026-11-27 (UTC)

## Latest continuation — premium Google Sign-In presentation — 2026-11-27

- UI source commit: `aa6ef7fcfb30cd2e3b653dd1084bbf6e1e450af9` on `feat/auth-google-category-home-20261127`; the existing PR #18 remains the only target branch.
- Login and account-link panels now use a premium emerald/glass and champagne-gold frame, Nanou monogram, secure-identity label, responsive spacing and reduced-motion-safe hover treatment. The interactive control remains Google's official Identity Services button (`filled_black`, large pill, left logo, 300 px width); no imitation button was added.
- Local checks on this exact code: `tests/test_web_platform.py::test_login_first_google_signup_link_and_category_home_are_served` — **1 passed**; `tests/test_auth.py -k google` — **5 passed, 15 deselected**; `node --check`, `python -m compileall -q src tests`, and `git diff --check` — PASS.
- Previous READY Preview deployment `dpl_DuFj3kBATf2MzLNBrQnJnSfWaaE4` is on prior SHA `c4733a9f159370c2654eec787e6d55303468e241`; the new UI commit still needs to be pushed and its Git-linked Preview / exact-head checks verified.
- Vercel Preview environment still lacks `NANOU_GOOGLE_CLIENT_ID`. The premium card is implemented, but real Google Sign-In remains disabled until a Google OAuth Web Client ID and the authorized Preview origin are configured. No Google credential, Production environment, user/session, or role was changed.
- No merge to `main`, Production deployment, Production database/configuration or SSO change was made.

## Current PR #18 Preview verification — 2026-11-27

This addendum supersedes older PR #18, Google Sign-In, and branch-preview notes below. Production state is unchanged.

- Repository: `pascalnanousympathie-alt/nanou-cyber-defense-ai`; branch `feat/auth-google-category-home-20261127`; source SHA at verification: `84437293a544496935f3fe09ed74cc6d972425aa`.
- PR #18 is OPEN, Draft, and mergeable; it is not merged. The current source commit is identical to the remote branch. No merge or Production deployment was performed.
- GitHub Code Scanning alert #1 (`py/weak-sensitive-data-hashing`) was dismissed as `false positive` with a 280-character rationale. The review confirmed `_hmac_fingerprint` receives only normalized email/IP identifiers; password create/change/verify paths use Argon2id. The alert is absent from the open-alert list for `refs/pull/18/merge`.
- PR #18 required checks: 9/9 SUCCESS, including aggregate CodeQL, CodeQL Python, CodeQL JavaScript/TypeScript, Gitleaks, CI tests, dependency audit, ML smoke, Vercel and Preview comments. CI previously reported 163 passed / 4 skipped.
- Vercel Preview deployment `dpl_J4oT2WsK37nuwjVZXuYHZ9PZ5v3s` is READY on the exact source SHA. Immutable URL: `https://nanou-cyber-defense-7l9ujtif0-nanou3.vercel.app/`; branch alias: `https://nanou-cyber-defense-ai-git-feat-auth-google-categ-90207d-nanou3.vercel.app/`.
- Live Preview smoke: `/ready` HTTP 200 (`database=postgresql`); `/api/auth/me` HTTP 200 unauthenticated; `/api/admin/users` HTTP 401 unauthenticated. Locale runtime check: all 12 locales passed, no untranslated `data-i18n` values, language selectors synchronized, Arabic RTL passed; page restored to French.
- Neon Preview only: project `young-snow-19049684`, branch `br-long-field-bianlzu3`, database `nanou_preview`. Table `public.google_identities` was created additively as `nanou_preview_app`, which owns `public.users` and already has the required schema/REFERENCES privileges. No role or grant was created or changed. The table has the FK to `users(id)` and unique `user_id`; owner is `nanou_preview_app`. `nanou_preview_runtime` has SELECT/INSERT/UPDATE/DELETE and no TRUNCATE. A no-row INSERT privilege probe and runtime SELECT passed; identity row count remains zero.
- Vercel environment metadata was read without decrypting values. `NANOU_GOOGLE_CLIENT_ID` is absent. The live `/api/auth/providers` response after the Preview migration is HTTP 200 with `google.enabled=false`, reason `client_id_missing`; this proves the schema gate is clear and the remaining Google blocker is the OAuth Web Client ID.
- Owner action still required: create/use a Google OAuth Web client, add the exact PR #18 Preview branch origin to Authorized JavaScript origins, then set `NANOU_GOOGLE_CLIENT_ID` on Vercel Preview only and redeploy Preview. Keep Production OAuth configuration separate until explicitly approved. No Google Client Secret is needed in the browser for this GIS ID-token flow.
- Targeted local Google/Auth regressions: `6 passed, 31 deselected` using `python -m pytest` in `$HOME/.venvs/nanou-cyber-defense-termux`. An earlier direct `pytest` invocation used the global interpreter and failed collection because FastAPI was absent there; it was not a source-code test failure.
- Production Neon, Production environment variables, Production schema, Production Vercel deployment, SSO and live data were not changed.

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


## Current authoritative Production state — 2026-11-27 (supersedes older staged-cutover notes below)

- Repository visibility is **public**. PR #13 (daily backup cron resynchronization) merged to `main` as `cdeae3e34937a8e687585725b3d09b58bafa2eec`; the workflow is active with cron `43 2 * * *` UTC. No scheduled event has run after the change yet; the first expected validation point is 2026-11-28 02:43 UTC. Manual dispatch remains available.
- Vercel Production deployment `dpl_2gn4F1XNZazuevbDnbfAApW5xb1X` is READY on that exact `main` commit. Canonical `/ready` returned HTTP 200 and `{"status":"ready","database":"postgresql"}`. Main `settings.py` prefers `NANOU_RUNTIME_DATABASE_URL` and returns no DB URL on Vercel/AWS Lambda if it is missing; Vercel metadata confirms the Production-only sensitive `NANOU_RUNTIME_DATABASE_URL` variable exists (value intentionally not decrypted).
- Production ownership transfer is **APPLIED and directly verified** on Neon main (`br-damp-fog-bi0lzjf4`, database `nanou_cyber_defense`). A fresh read-only catalog query using the explicitly selected `nanou_app` connection confirmed `nanou_migration_owner` owns the database, all 9 application tables and both sequences (11 public objects total). `nanou_app` owns none of these objects. The earlier SQL errors occurred only when the Neon query omitted the DB role; explicit `role_name` connections work.
- Post-cutover role checks: in a READ ONLY transaction, `nanou_migration_login` successfully executed `SET LOCAL ROLE nanou_migration_owner` (`session_user=nanou_migration_login`, `current_user=nanou_migration_owner`); the owner role is NOLOGIN/non-elevated and has database/public-schema CREATE, while the login has neither directly. `nanou_runtime` has SELECT/INSERT/UPDATE/DELETE on each of 9 tables, no TRUNCATE/TRIGGER/REFERENCES, and SELECT/USAGE (not UPDATE) on both sequences; database CREATE and public-schema CREATE are false. `nanou_backup` has SELECT only on all 9 tables and SELECT (not USAGE/UPDATE) on both sequences.
- Separate rehearsal branch `prod-role-transfer-rehearsal-20261126` (`br-morning-art-bi0ubfr1`) remains present and is not the Production database: in that branch `nanou_migration_owner` owns the 9 tables and 2 sequences, but `nanou_app` still owns the database. Do not confuse this rehearsal branch with the completed Production cutover.
- Legacy `nanou_app` remains login-enabled and retains elevated CREATEROLE/CREATEDB/REPLICATION/BYPASSRLS attributes and memberships (including `neon_superuser` and `nanou_migration_owner`), but the fresh catalog confirms it owns no current database, table or sequence. Do not disable or revoke it until a separate rollback and credential-retirement plan is reviewed and the application rollback path is established.
- Dependabot vulnerability alerts are enabled. Current state-filtered inventory: 1 OPEN HIGH alert for `signify` (`GHSA-p4hh-mq57-gq8x`, vulnerable range `<0.9.2`), and 0 `dismissed`, `fixed` or `auto_dismissed`. PR #14 upgrades to `signify==0.9.3` and its CI, ML smoke, dependency audit and security scans pass on head `9ce497a`; the alert remains OPEN until the fix is merged and GitHub refreshes the dependency graph.
- Owner browser profile is signed out: `/api/auth/me` returned `authenticated=false, bootstrap_required=false`; `/api/admin/users` returned 401 for the signed-out profile. Owner Admin browser acceptance and live Viewer/Analyst RBAC acceptance remain **PENDING OWNER SIGN-IN/TEST**. No credentials or bootstrap tokens are to be shared in chat.
- Private backup key remains local on Termux with filesystem mode `600`; an independent offline second copy is still **NOT VERIFIED** because no accessible removable/offline destination was mounted. Do not copy the private key to ordinary internal shared storage.
- Manual backup run `45946937978` completed SUCCESS on main commit `cdeae3e`; artifact `nanou-production-backup-45946937978` (23,362 bytes) exists. This run proves backup workflow/artifact creation only; it is not evidence of an ownership cutover or of a restore test for this specific artifact. The separately verified run `45941044613` passed checksum, authenticated decryption, `pg_restore --list`, and a full isolated local PostgreSQL restore with the 9 table row counts matching the Production read-only query. No scheduled `schedule` event has yet been observed after PR #13; first expected run is 2026-11-28 02:43 UTC.


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
- The retained `prod-restore-drill-20261126` branch is verified as a restored data copy, but a fresh 2026-11-27 catalog read shows `nanou_runtime_restore_probe` as database/table owner, `nanou_migration_owner_probe` as NOLOGIN, and no default-ACL rows. Do not cite its current state as proof of a full `nanou_migration_login` ownership cutover.
- New encrypted backup tools use RSA-3072 OAEP-SHA256 + AES-256-GCM, authenticated decryption and bounded streaming. Public key: `backups/production-backup-public.pem`; private key remains local on Termux with mode 600 and is not in Git.
- `.github/workflows/production-backup.yml` is staged, but scheduled backup is **BLOCKED / NOT ACTIVE** until Actions secret `NANOU_BACKUP_DATABASE_URL` is provisioned. No cleartext dump was uploaded; no automated backup artifact or automated restore has yet been proven. See `docs/production-backup-restore.md`.

### Production Neon roles

Production Neon project `cold-resonance-28231813`, default branch `main`, database `nanou_cyber_defense`:

- `nanou_runtime`: login role tested against all 9 tables / 60 columns. SELECT/INSERT/UPDATE/DELETE and sequence access work. No SUPERUSER, CREATEROLE, CREATEDB, BYPASSRLS, database CREATE, schema CREATE or TRUNCATE. Disposable DML probe was deleted; zero leftovers.
- `nanou_backup`: login role with SELECT only on all 9 tables and SELECT on both sequences; INSERT/UPDATE/DELETE/TRUNCATE/CREATE are not granted. Current snapshot data was readable (0 users, 2 audit events, 0 auth sessions).
- `nanou_migration_owner`: NOLOGIN; no SUPERUSER/CREATEROLE/CREATEDB/BYPASSRLS. Has the public-schema CREATE privilege required for controlled schema ownership/migrations. Default privileges are prepared: runtime receives table DML and sequence usage; backup receives SELECT only.
- `nanou_migration_login`: login role with no SUPERUSER/CREATEROLE/CREATEDB/REPLICATION/BYPASSRLS and no direct public-schema CREATE. A read-only 2026-11-27 connection test successfully executed `SET LOCAL ROLE nanou_migration_owner`; the effective role was NOLOGIN, non-elevated, and had public-schema USAGE/CREATE. No DDL was executed in this check; do not treat it as a create/drop smoke test.
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
- This verifies encrypted-artifact decrypt/restore to local PostgreSQL. A Neon branch restore of this exact artifact now PASSes on `br-little-sound-bipv6bjm` (`prod-restore-drill-20261126`), database `nanou_restore_drill_20261126`, using the isolated `nanou_runtime_restore_probe` role. The Production main branch row counts were queried read-only afterward and remained identical (users=0, audit_events=2, auth_attempts=4, auth_sessions=0, platform_state=1). A second offline recovery copy of the private key remains outstanding. The private key stays local with mode 600.

### Production deployment and cutover

- Latest Vercel Production deployment remains READY on old commit `46afde6042841715364f416623a416022a8476d1`; it has not yet deployed the current `main` runtime selector/HMAC code.
- Attempted exact-HEAD Production deployment of `fe47b815fa90bd2bacd06d4ab4e139e874fce88b` was rejected with Vercel HTTP 402 `api-deployments-free-per-day` (more than 100 deployments/24h; retry-after 86400 seconds). Vercel CLI was not installed/authenticated on the Nanou Termux device; no CLI bypass, plan upgrade or quota change was attempted.
- Production `nanou_runtime`, `nanou_backup`, `nanou_migration_owner` (NOLOGIN), and `nanou_migration_login` are staged. `nanou_app` still owns the Production database/tables and has elevated privileges. Do not transfer ownership or revoke legacy credentials before a tested runtime deployment and rollback window.
- GitHub main ruleset `28156409` protects source with PR/strict checks. Neon Production branch protection remains constrained by the Free-plan protected-branch quota.
- Production user count remains zero and bootstrap is not claimed. Owner Admin bootstrap plus live Viewer/Analyst registration, approval, RBAC and logout/re-login acceptance are still required. Keep Vercel SSO enabled.

No Production ownership transfer, migration, credential retirement, new Production deployment, SSO removal, paid upgrade or public launch occurred in this continuation.

## Production verification — 2026-11-27 (current evidence)

This section supersedes older statements above that Production had zero users or that the first-admin bootstrap was still pending.

### Source, CI and deployment

- main was checked against commit a6e15da951641f2f6983c01afc8f8b0484fd3f31; GitHub compare returned identical.
- PR #11 is merged. CI run 45889588789 completed successfully: Ruff lint/format, test job, dependency audit and ML smoke all passed.
- Security run 45889588961 completed successfully: CodeQL Python, CodeQL JavaScript/TypeScript and Gitleaks full-history/ref scan all passed.
- Current Vercel Production deployment dpl_2AxU3iCjEYUWkJRp4iSDrCwbWSur is READY on main commit a6e15da. Build log ended with “Deployment completed”.
- Live checks through the connected Opera browser: /health returned HTTP 200 (status=ok); /ready returned HTTP 200 (status=ready, database=postgresql).
- Vercel SSO protection remains enabled for all deployment types.

### Bootstrap and account state — Production Neon

Read-only verification against Production project cold-resonance-28231813, branch br-damp-fog-bi0lzjf4, database nanou_cyber_defense:

- platform_state.bootstrap_claimed=true.
- Exactly one user exists; role aggregate shows one admin with is_approved=true and is_active=true.
- One authentication session exists and is not expired. No session token, token hash, password hash or account email was retrieved.
- Audit aggregate records one auth.bootstrap event with outcome success.
- Vercel NANOU_BOOTSTRAP_TOKEN metadata is sensitive/secret and Production-only. Its value was not decrypted or read. Production NANOU_RUNTIME_DATABASE_URL and NANOU_AUDIT_HMAC_KEY are also present as sensitive Production variables; values were not read.

### Runtime role and remaining database hardening

- Main's current settings code prioritizes NANOU_RUNTIME_DATABASE_URL and fails closed on serverless hosting if it is absent.
- nanou_runtime has login enabled and no SUPERUSER, CREATEROLE, CREATEDB, REPLICATION or BYPASSRLS attributes. It has SELECT/INSERT/UPDATE/DELETE on application tables, but no TRUNCATE or public-schema CREATE.
- nanou_app still owns the public application tables and retains CREATEROLE, CREATEDB, REPLICATION and BYPASSRLS attributes; it is still a member of neon_superuser and nanou_migration_owner. nanou_migration_owner is NOLOGIN and has no elevated role attributes.
- Do not transfer Production ownership, revoke the legacy role, or change grants until the reviewed cutover/rollback plan is explicitly approved and the live application role is confirmed throughout the rollback window.

### RBAC acceptance and current browser context

- Source tests cover one-time bootstrap, pending Viewer registration, approval/role changes, session revocation, protection of the last active Admin, Viewer read-only permissions, Admin-only audit access, CSRF and logout.
- Production currently contains only the Admin account. Separate live Viewer and Analyst registration/approval and end-to-end role acceptance are NOT VERIFIED.
- The Opera Connector browser profile used for this verification is signed out of the application: /api/auth/me returned authenticated=false, bootstrap_required=false; /api/admin/users returned 401. This is expected for that signed-out profile and does not invalidate the Production Admin bootstrap verified in Neon. The user must sign in using their own browser/profile; credentials must not be shared in chat.
- Admin logout/re-login, password-change acceptance, and live role-specific UI/API tests remain pending.

### Backup and operational gates

- Previously verified encrypted Production backup runs 45850155507 and 45852927966 succeeded; the latter's encrypted artifact was checksum-verified and restored to isolated local PostgreSQL and an isolated Neon restore branch. These results are historical evidence from 2026-11-26, not a fresh backup run in this verification.
- A second offline recovery copy of the private backup key remains NOT VERIFIED. Keep the private key off Git and out of chat.
- Production remains deployed and healthy, but unrestricted public-launch readiness is NOT VERIFIED. Remaining gates include live Viewer/Analyst acceptance, confirmed Admin session acceptance in the owner's browser, an independent security review/CodeQL alert inspection, backup-key recovery copy, monitoring/incident-response acceptance, and controlled database-role ownership cutover.


## Latest runtime-role and backup automation verification — 2026-11-27

- Production deployment `dpl_2AxU3iCjEYUWkJRp4iSDrCwbWSur` remains READY on main commit `a6e15da951641f2f6983c01afc8f8b0484fd3f31`.
- The deployed settings code prioritizes the dedicated `NANOU_RUNTIME_DATABASE_URL` and fails closed on serverless hosting when it is absent. Vercel metadata confirms the sensitive Production runtime URL exists; its value was not decrypted.
- Live `/ready` returned PostgreSQL-ready. A read-only database activity query immediately afterward observed an idle PgBouncer connection for `nanou_runtime`, directly confirming that the deployed app exercised the restricted runtime login.
- Fresh PostgreSQL role metadata: `nanou_runtime` has no elevated role flags and no membership in `neon_superuser` or `nanou_migration_owner`; `nanou_backup` is also restricted. The legacy `nanou_app` still has CREATEROLE, CREATEDB, REPLICATION, BYPASSRLS and elevated role memberships and remains in place as database/table owner. No grants, ownership, credentials or Production deployment were changed.
- Backup automation gap: workflow YAML includes the daily 02:17 UTC cron and manual dispatch, but GitHub Actions main-branch history through 2026-11-27T04:34Z shows only successful manual backups `45850155507` and `45852927966` on 2026-11-26; no scheduled run for 2026-11-27 is evidenced. Workflow enabled/disabled state was not independently proven. Mark scheduled backup as NOT VERIFIED until a scheduled run and resulting encrypted artifact are confirmed.
- The two earlier manual backup artifacts remain successfully checksum-verified and restored to isolated local PostgreSQL and isolated Neon restore branch. A second offline recovery copy of the private key remains NOT VERIFIED.
- Current runtime error query found no clusters in the preceding 24 hours; production error/fatal log query found no records in its 50-minute window.
- Remaining operational gates: diagnose/confirm scheduled backup execution; verify the separate private-key recovery copy; complete owner Admin-browser and Viewer/Analyst RBAC acceptance; inspect CodeQL alerts; prepare and approve the controlled database ownership cutover/rollback. No Production ownership/grant changes or launch/merge occurred.


## Encrypted backup full-restore and scheduler follow-up — 2026-11-27

- GitHub Actions backup run [45941044613](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45941044613) completed successfully on main commit `a6e15da951641f2f6983c01afc8f8b0484fd3f31`. The read-only `nanou_backup` preflight, `pg_dump`, RSA-3072 OAEP-SHA256 + AES-256-GCM encryption and artifact upload all passed.
- Artifact `nanou-production-backup-45941044613` (ID `15172521803`) has GitHub ZIP SHA-256 `be57978e1000edbc00a35111eef4ed23b89e69664ac62f617222a6fe36612380`, size 22,702 bytes, and expires 2026-12-27. Its encrypted payload sidecar checksum returned `OK`.
- The artifact was authenticated-decrypted on the authorized Nanou Termux device using the existing private key (mode 600); `pg_restore --list` passed. A separate disposable PostgreSQL cluster on port 55440 then completed a full `pg_restore --exit-on-error --single-transaction --clean --if-exists --no-owner --no-privileges` restore.
- Restored counts matched a read-only Production count query across all nine tables at verification time: `api_keys=0`, `attack_scopes=0`, `attack_simulations=0`, `audit_events=3`, `auth_attempts=2`, `auth_sessions=1`, `malware_metadata=0`, `platform_state=1`, `users=1`.
- The first disposable restore attempt hit the standard pre-existing `public` schema collision in the template database. It was corrected by restoring with `--clean --if-exists` in the isolated disposable database; no Production connection or object was changed.
- Cleanup verified: the temporary restore directory was absent, no PostgreSQL process remained on port 55440, and the pre-existing Termux PostgreSQL service remained online at its original port 5432 and original data directory.
- Backup automation: GitHub reports workflow `Production database backup` as `active`; repository default branch is `main`, and the workflow file is on `main`. The scheduled-event run list is still empty, while manual dispatch succeeds. Latest workflow-file commit was authored by the same currently authenticated repository account on 2026-11-26. Public-repository 60-day inactivity auto-disable is inconsistent with the recent repository activity, but no schedule event is evidenced for 2026-11-27.
- GitHub documents that scheduled runs can be delayed/dropped under Actions load, and that schedules may stop while manual dispatch still works if the workflow-associated actor is suspended/deprovisioned. The connected account is authenticated now; we cannot independently verify GitHub's historical schedule actor state. See [GitHub scheduled workflow troubleshooting](https://docs.github.com/en/actions/how-tos/troubleshoot-workflows) and [schedule event reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows).
- Recovery-key copy: the original private key remains on the Nanou device with mode 600 and its existing public-key fingerprint had previously matched. Scoped shared-storage inventory found no matching PEM in the shared backup/Download paths and exposed only Android emulated/self storage roots; no separate offline recovery copy or removable destination is verified. Do not copy the private key into ordinary shared storage.
- Code Scanning query returned 0 open alerts. Dependabot alert listing remains inaccessible through the connected GitHub permissions; do not infer zero Dependabot alerts.


## Production migration-role verification — 2026-11-27 (read-only)

- Current Production catalog shows `nanou_migration_owner` is NOLOGIN, has no SUPERUSER/CREATEROLE/CREATEDB/REPLICATION/BYPASSRLS, and has public-schema USAGE/CREATE.
- `nanou_migration_login` is login-enabled, has no elevated flags and no direct public-schema CREATE. Its `pg_auth_members` membership has `set_option=true` for `nanou_migration_owner`.
- A connection using `nanou_migration_login` successfully ran `SET LOCAL ROLE nanou_migration_owner` inside a read-only transaction. Session login remained `nanou_migration_login`; effective role was `nanou_migration_owner`.
- Production default ACLs owned by `nanou_migration_owner` are present: new tables grant `nanou_runtime` DML and `nanou_backup` SELECT; new sequences grant `nanou_runtime` SELECT/USAGE and `nanou_backup` SELECT.
- Aggregate privilege check over all 9 Production tables and 2 sequences: `nanou_runtime` has DML and sequence access but no TRUNCATE/TRIGGER/REFERENCES excess; `nanou_backup` has SELECT-only table access. `nanou_app` still owns the database and all 9 tables and retains elevated role attributes/memberships.
- This is role/membership/default-ACL preparation evidence, not ownership-transfer evidence. No Production DDL, owner change, grant change, credential retirement or deployment was performed. The complete ownership cutover and rollback window remain outstanding.
