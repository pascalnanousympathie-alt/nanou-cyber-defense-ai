# Production backup and restore

## Current Production cutover state — 2026-11-27

This section supersedes earlier staged-cutover statements below.

- Production ownership transfer is **APPLIED and directly verified** on main branch `br-damp-fog-bi0lzjf4`: NOLOGIN `nanou_migration_owner` owns the database, all 9 application tables and both sequences. Fresh read-only catalog queries succeeded using explicit DB roles. Legacy `nanou_app` owns none of these objects but retains elevated role attributes/memberships; do not retire it before rollback and credential-retirement review.
- Post-cutover checks confirm `nanou_migration_login` can `SET LOCAL ROLE nanou_migration_owner` in a READ ONLY transaction; runtime has SELECT/INSERT/UPDATE/DELETE on all 9 tables, no excess TRUNCATE/TRIGGER/REFERENCES, and sequence SELECT/USAGE only; backup has SELECT only on tables and sequence SELECT without USAGE/UPDATE. Runtime has no database or schema CREATE.
- The separate Neon branch `prod-role-transfer-rehearsal-20261126` (`br-morning-art-bi0ubfr1`) remains an isolated rehearsal, not Production: it has `nanou_migration_owner` for the tables/sequences but `nanou_app` for the database. Production main ownership was verified independently as described above.
- Legacy `nanou_app` remains login-enabled and retains CREATEROLE/CREATEDB/REPLICATION/BYPASSRLS and memberships including `neon_superuser`, but the Production database and 11 tables/sequences are now owned by `nanou_migration_owner`. Do not revoke, disable, drop or rotate its credential until a separate rollback and credential-retirement plan is reviewed and the application rollback path is established.
- Vercel Production deployment `dpl_2gn4F1XNZazuevbDnbfAApW5xb1X` is READY on main commit `cdeae3e34937a8e687585725b3d09b58bafa2eec`; `/ready` returns PostgreSQL ready. Main code prefers `NANOU_RUNTIME_DATABASE_URL` and fails closed on Vercel if it is absent; Vercel metadata confirms the Production-only sensitive variable exists (value not decrypted).
- PR #13 merged the cron update to `43 2 * * *` UTC. The workflow is active, but no real scheduled event has been observed after that change; the first expected run is 2026-11-28 02:43 UTC. Manual run `45946937978` completed successfully on main commit `cdeae3e` and produced artifact `nanou-production-backup-45946937978` (23,362 bytes). This confirms backup/artifact creation only. The separately verified artifact from run `45941044613` passed checksum, authenticated decryption, `pg_restore --list` and a full isolated local PostgreSQL restore with all 9 table row counts matching the read-only Production query.
- Dependabot vulnerability alerts are enabled. Current inventory: 1 OPEN HIGH `signify` alert (`GHSA-p4hh-mq57-gq8x`, vulnerable `<0.9.2`) and zero dismissed/fixed/auto-dismissed alerts. PR #14 proposes the patched `signify==0.9.3` with passing CI/ML smoke/dependency-audit/security checks; it remains unmerged, so the alert is still open.
- The private decryption key remains on the authorized Termux device with mode 600. Its independent offline second copy remains NOT VERIFIED because no accessible separate removable/offline destination is currently mounted. Never put the private key in Git, Vercel or chat.


## Backup design

The Production backup path is designed around three separate credentials:

- `nanou_runtime`: application login; SELECT/INSERT/UPDATE/DELETE and sequence access only.
- `nanou_backup`: backup login; SELECT only across the nine application tables and sequence state.
- `nanou_migration_owner`: NOLOGIN owner for future schema objects. A separate `nanou_migration_login` can SET ROLE to it for reviewed DDL; it has no CREATEROLE, CREATEDB or BYPASSRLS privilege itself.

Do not use `nanou_app` as the long-term runtime or backup identity. It remains the current database/table owner during the staged cutover and must not be removed until the application has switched to `nanou_runtime` and the rollback window is closed.

## Manual snapshot and restore evidence

- Production Neon project: `cold-resonance-28231813`, default branch `main`.
- Snapshot: `prod-pre-hardening-2026-11-26` (`snap-shiny-fire-bir6x6kk`).
- Restore drill branch: `prod-restore-drill-20261126` (`br-little-sound-bipv6bjm`).
- Source and restored schema comparison: 9 application tables and 60 columns matched.
- Snapshot row comparison covered all application tables; the observed non-zero counts included 2 audit events, 4 auth attempts and 1 platform_state row at snapshot time.
- The retained Production restore branch `prod-restore-drill-20261126` (`br-little-sound-bipv6bjm`) is an isolated data-restore copy. A fresh read-only catalog check on 2026-11-27 showed `nanou_runtime_restore_probe` as DB/table owner, `nanou_migration_owner_probe` as NOLOGIN, and no default ACL rows. Its current state is not proof of a completed migration-login ownership cutover.
- A separate Neon project `nanou-cyber-defense-restore-drill` (`curly-credit-07474065`, branch `restore-test`) contains a prototype fixture: `restore_owner` owns its `nanou_restore` DB/tables, and `nanou_runtime_probe` is NOLOGIN with default table-DML and sequence SELECT/USAGE grants. This validates a privilege pattern only; it is not the Production migration cutover.

## Encrypted backup file format

The backup utility in `nanou_cyber_ai.backup.crypto` implements:

- RSA-3072 OAEP with SHA-256 for wrapping a fresh random 256-bit data key.
- AES-256-GCM for streaming encryption and authenticated integrity.
- AAD binds the ciphertext to the Nanou Production backup format/version.
- Bounded 1 MiB streaming, temporary file, fsync and atomic replace.
- Decryption writes to a temporary file and only publishes it after GCM authentication succeeds.
- The decrypt command rejects tampering, truncated data and RSA keys below 3072 bits.

The public recipient key is `backups/production-backup-public.pem`. The matching private key is stored locally on the authorized Termux device at:

`~/.local/share/nanou-cyber-defense-ai/backup-keys/production-backup-private.pem`

The private key was created locally with filesystem mode 600. Never commit it, upload it to GitHub, print it to logs or send it in chat. Keep an offline recovery copy before relying on encrypted artifacts as the only backup.

### Local commands

Install the optional backup dependency:

```sh
python -m pip install -e '.[backup]'
```

Encrypt a previously generated PostgreSQL custom-format dump:

```sh
python scripts/encrypt_production_backup.py \
  --input production.dump \
  --public-key backups/production-backup-public.pem \
  --output production-backup.ncdb
sha256sum production-backup.ncdb > production-backup.ncdb.sha256
```

Decrypt only to a controlled isolated restore location:

```sh
python scripts/decrypt_production_backup.py \
  --input production-backup.ncdb \
  --private-key ~/.local/share/nanou-cyber-defense-ai/backup-keys/production-backup-private.pem \
  --output production.dump
pg_restore --list production.dump
```

Never restore directly over the Production database as a first validation. Restore into a new isolated branch/database, compare schema and row counts, run application checks, and record RPO/RTO before a controlled cutover.

## Scheduled GitHub Actions backup

Workflow: `.github/workflows/production-backup.yml`.

- Runs daily at 02:43 UTC or via manual dispatch, only from `main`.
- Uses the read-only `nanou_backup` connection.
- Runs PostgreSQL 17 `pg_dump --format=custom --no-owner --no-privileges`, validates with `pg_restore --list`, encrypts the dump, writes SHA-256 and a manifest, then uploads only the encrypted artifact.
- GitHub artifact retention is 30 days.
- The workflow requires repository Actions secret `NANOU_BACKUP_DATABASE_URL`; it must contain the direct-host PostgreSQL URL for `nanou_backup`, not the runtime or owner credential.

**Current status: MANUAL BACKUPS SUCCEED; SCHEDULE DELIVERY NOT YET VERIFIED.** PR #13 has merged the daily cron update to `43 2 * * *` UTC. The workflow remains active and manual dispatch works. No `schedule` event after the change is currently visible; the next expected scheduled attempt is 2026-11-28 02:43 UTC. Manual run `45946937978` produced an encrypted artifact; run `45941044613` is the artifact with separately verified authenticated decrypt and isolated local restore. Never place the connection URI in source code, logs, or chat.

## Production cutover gates

1. Confirm the current Production app has deployed code that selects `NANOU_RUNTIME_DATABASE_URL` and fails closed when it is absent.
2. Confirm the exact Production runtime URL with the `nanou_runtime` role and run read-only health plus disposable DML smoke tests.
3. Confirm a fresh backup exists and decrypt/restore it in an isolated destination.
4. Transfer database/tables/sequences to the NOLOGIN `nanou_migration_owner`; establish default grants for `nanou_runtime` and `nanou_backup`.
5. Verify login `nanou_migration_login` can only perform reviewed DDL after `SET ROLE nanou_migration_owner`.
6. Deploy and smoke-test the exact production candidate; then retire the old `nanou_app` credential only after the rollback window is closed.
7. Preserve Vercel SSO and retain a documented recovery path.

No Production ownership transfer, old-role deletion, merge to `main`, or Production deployment is performed by this runbook alone.


## Latest exact-head validation and operational evidence — 2026-11-26

- Latest previously validated PR #5 head before the latest preflight refinement: `0638a749c8bef2a98a4616d8861c4299ba7b968c`.
- CI run [45827291114](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45827291114): PASS — Ruff lint/format; 51 tests passed / 4 skipped; ML smoke 13 passed; dependency audit reported no known vulnerabilities.
- Security run [45827291100](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45827291100): PASS — Gitleaks found no leaks; CodeQL Python passed. CodeQL JavaScript/TypeScript completed with an explicit not-applicable skip because main has no non-empty tracked JS/TS sources.
- Backup URI parsing lives in the installed `nanou_cyber_ai.backup.connection` package. It requires a PostgreSQL URI, username/password/database, TLS mode, unique supported query options and rejects arbitrary `options` / `PGOPTIONS`. The wrapper script imports this package.
- The backup workflow requires exact login `nanou_backup`, rejects membership in any other PostgreSQL role, database/schema CREATE and table/sequence write privileges, and dumps only `public`.
- Direct read-only Production queries executed as `nanou_backup` confirmed SELECT access to all nine application tables and both public sequences; no table write privileges, no sequence USAGE/UPDATE, and no extra role memberships. The role has `public` schema USAGE. RLS and FORCE RLS are disabled on all nine application tables. Thus, the current schema does not cause `pg_dump` to omit rows due to RLS, and sequence state can be read without granting sequence write privileges.
- The latest workflow verifies public-schema USAGE, SELECT on every public sequence, and absence of RLS/FORCE RLS on public tables before dumping. Exact-head CI/Security subsequently passed on PR #5 at `2458f8bba97a762478a426c14f150ecd3a048871` and again on the follow-up documentation commit.
- The crypto tests use an ephemeral RSA keypair to prove streaming round-trip, authentication-tag tamper rejection, and rejection of RSA keys below 3072 bits. This is cryptographic unit-test evidence only; it is not an actual Production artifact restore rehearsal.
- The first post-merge manual backup run [45850155507](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45850155507) completed successfully and uploaded the encrypted artifact `nanou-production-backup-45850155507`. Details, size, expiry and checksum are recorded in the execution evidence below.
- On Desktop Commander device Nanou, the private key was re-verified as present with filesystem mode `600`; its derived public-key SHA-256 fingerprint matches the pinned recipient key. A separate offline recovery copy has not yet been verified.
- Production database ownership remains with `nanou_app`. PR #6 merged the `[tool.vercel] entrypoint` fix in commit `46afde6042841715364f416623a416022a8476d1`; the resulting Vercel Production deployment `dpl_Xoz7AtnCrfoaPaghxJ3eyj62FjQP` is READY. The canonical Production alias returns HTTP 200 for `/health`, `/openapi.json`, and `/api/mcp/tools`. The metadata API is intentionally fail-closed and returns HTTP 503 until `NANOU_METADATA_API_TOKEN` is provisioned. No Admin bootstrap, database ownership transfer, or credential revocation was performed.
- Neon rejected protecting Production branch `main` with HTTP 422 because the current plan's protected-branch quota is full. No other branch protection was removed and no paid upgrade was made.


## Current verification — 2026-11-26

- Exact PR head: `2458f8bba97a762478a426c14f150ecd3a048871`.
- CI run [45829753859](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45829753859): PASS — Ruff lint/format; 51 passed / 4 skipped; ML smoke 13 passed; pip-audit found no known vulnerabilities.
- Security run [45829753884](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45829753884): PASS — Gitleaks found no leaks; CodeQL Python succeeded; JavaScript/TypeScript was explicitly not applicable because this ref contains no non-empty tracked JS/TS source files.
- GitHub Actions secret `NANOU_BACKUP_DATABASE_URL`: present (secret name verified; secret value not printed).
- On Desktop Commander device Nanou, the local private key exists with mode `600`; its derived public-key SHA-256 fingerprint matches the pinned recipient fingerprint `f5cb681b49a315ee94dccf420fdef26b92ac002c723f85544a0b5dd77b6fa7c1`. A separate offline recovery copy has not yet been verified.
- The workflow remains restricted to `refs/heads/main`. PR #5 is merged; manual workflow_dispatch runs `45850155507` and `45852927966` both succeeded, and two encrypted artifacts exist. The second artifact's portable checksum was verified on the authorized Termux device with `sha256sum -c`. No post-download authenticated decrypt-and-restore rehearsal has been completed.


## First encrypted Production backup execution — 2026-11-26

- PR #5 was merged to `main` in merge commit `a7669d7e6969a647c6f78a8edb02085179ae646c`.
- The first manual workflow dispatch, [run 45850155507](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45850155507), completed with conclusion **success** on that merge commit.
- All operational steps succeeded: recipient-key validation, read-only Production database preflight, `pg_dump`, in-runner `pg_restore --list` archive-index validation, RSA-OAEP-SHA256 + AES-256-GCM encryption, and artifact upload.
- Uploaded artifact: `nanou-production-backup-45850155507`; artifact ID `15134116099`; archive size 22,336 bytes; created 2026-11-26 15:33:27 UTC; expires 2026-12-26 15:33:26 UTC.
- Encrypted payload: `nanou-production-20261126T153326Z.ncdb`, 21,610 bytes. It was downloaded to the authorized Nanou Termux device and independently compared with its sidecar digest: `3aa2be9e6cae503e0e69321c91872954d0157c09eafddcad03699b402bf43c02` — **match**.
- Initial sidecar recorded the GitHub runner's absolute path, so `sha256sum -c` failed on the Termux device due to path mismatch; direct hash comparison confirmed the bytes match. PR #6 changes sidecar creation to store only the payload basename.
- The private key remained on the authorized device and was not uploaded or sent in chat. A separate offline recovery copy and an authenticated decrypt/isolated restore rehearsal are still outstanding.
- The workflow runs daily at 02:17 UTC, with artifacts retained for 30 days.

## Vercel FastAPI build diagnosis — 2026-11-26

- The merge commit triggered a Vercel Production build that failed at the build step with `FASTAPI_ENTRYPOINT_NOT_FOUND`.
- Vercel identified `src/nanou_cyber_ai/api.py` and its `app` object as the valid application entrypoint, and recommended `[tool.vercel] entrypoint = "src.nanou_cyber_ai.api:app"`.
- The same missing Vercel configuration was present in the parent `main` commit before PR #5, so this was a pre-existing project configuration defect, not a backup workflow failure. PR #6 subsequently corrected it.
- The PR #6 Preview deployments reached READY. After PR #6 merged, Production deployment `dpl_Xoz7AtnCrfoaPaghxJ3eyj62FjQP` reached READY on commit `46afde6042841715364f416623a416022a8476d1`.


## PR #6 validation — 2026-11-26

- PR: [#6 — Fix Vercel FastAPI entrypoint and portable backup checksum](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/pull/6).
- At validated head `e9430b037bdd77fa425459bede296452057e65b7`, CI run [45851810022](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45851810022) passed: Ruff lint/format; 51 tests passed / 4 skipped; ML smoke 13 passed; dependency audit found no known vulnerabilities.
- Security run [45851809676](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45851809676) passed: Gitleaks, CodeQL Python and CodeQL JavaScript/TypeScript.
- Vercel generated Preview deployment `dpl_89tdV6FXpuKZUhMDUEqN8ZWb52Mw`, which reached **READY** with the FastAPI entrypoint configured. After merge, Production deployment `dpl_Xoz7AtnCrfoaPaghxJ3eyj62FjQP` also reached **READY**. Authenticated Vercel fetch confirmed `/health` HTTP 200 and `/openapi.json` HTTP 200.
- The revised relative checksum command was exercised with a synthetic test payload on the authorized Termux device; `sha256sum -c` returned `OK`. The next actual Production backup should verify the new sidecar format on the uploaded artifact.
- PR #6 merged on 2026-11-26 at 15:49:14 UTC in commit `46afde6042841715364f416623a416022a8476d1` after CI, Security and Preview validation passed.


## Second encrypted Production backup execution — 2026-11-26

- The second manual workflow dispatch, [run 45852927966](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45852927966), completed with conclusion **success** on main commit `46afde6042841715364f416623a416022a8476d1`.
- Recipient-key validation, read-only Production database preflight, `pg_dump`, in-runner `pg_restore --list`, encryption and artifact upload all succeeded.
- Artifact `nanou-production-backup-45852927966`, ID `15132954840`, ZIP size 22,294 bytes, created 2026-11-26 15:50:21 UTC; expires 2026-12-26 15:50:20 UTC.
- Encrypted payload `nanou-production-20261126T155020Z.ncdb`, 21,610 bytes. Downloaded to the authorized Nanou Termux device; the sidecar contains a portable relative filename and `sha256sum -c` returned **OK** from the extracted artifact directory.
- Payload SHA-256: `7d10aa52c03d4fe03b00244a37c539bf019a79992271b476f27c19f4da308f81`.
- Manifest format check passed: `RSA-3072-OAEP-SHA256+AES-256-GCM`.
- No plaintext dump was restored to Production. Post-download authenticated decryption and isolated restore verification remain outstanding.

## Final deployment and CI evidence — 2026-11-26

- PR #6 merged to `main` as `46afde6042841715364f416623a416022a8476d1`.
- Post-merge CI [45852852858](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45852852858): **PASS** — Ruff lint/format, 51 passed / 4 skipped, ML smoke 13 passed, dependency audit found no known vulnerabilities.
- Post-merge Security [45852852502](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45852852502): **PASS** — Gitleaks and CodeQL Python. JavaScript/TypeScript CodeQL was not applicable because no non-empty tracked JS/TS source files exist on this ref.
- Vercel Production deployment `dpl_Xoz7AtnCrfoaPaghxJ3eyj62FjQP` is **READY** on the merge commit. The canonical alias `https://nanou-cyber-defense-ai.vercel.app` returned HTTP 200 for `/health`, `/openapi.json` and `/api/mcp/tools`.
- OpenAPI confirms HTTP Bearer protection on `/api/malware/metadata`. A GET without the optional `NANOU_METADATA_API_TOKEN` returned HTTP 503 with a fail-closed message; this feature remains disabled until its owner intentionally configures the token.
- The private decryption key remains local to the authorized device (mode `600`; public fingerprint matches the pinned recipient key). A second offline recovery copy has not been verified. The private key was not copied to GitHub, Vercel, or chat.

## Authenticated encrypted-artifact restore rehearsal — 2026-11-26

- GitHub Actions backup run `45852927966` completed successfully on `main`; the repository secret name `NANOU_BACKUP_DATABASE_URL` is present. The secret value was not read or displayed.
- Downloaded encrypted artifact: `nanou-production-20261126T155020Z.ncdb`; SHA-256 `7d10aa52c03d4fe03b00244a37c539bf019a79992271b476f27c19f4da308f81`. `sha256sum -c` returned **OK**.
- Authenticated RSA-OAEP-SHA256/AES-256-GCM decryption succeeded using the private key stored locally with mode `600`; `pg_restore --list` succeeded.
- Restored the archive into a temporary, isolated local PostgreSQL 18.2 cluster on the Nanou Termux device. Result: **9 tables / 60 columns**, `users=0`, `audit_events=2`, `auth_attempts=4`, `auth_sessions=0`, `platform_state=1`. These counts match the documented snapshot-time evidence.
- The temporary local PostgreSQL cluster was stopped and removed after the test. Production Neon was not used as the restore target and was not modified.
- This proves authenticated decrypt and PostgreSQL archive restore locally. The same artifact was then restored with `pg_restore --single-transaction --clean --if-exists --no-owner --no-privileges` into isolated Neon branch `br-little-sound-bipv6bjm` (`prod-restore-drill-20261126`), database `nanou_restore_drill_20261126`, using `nanou_runtime_restore_probe`. Restore result: 9 tables / 60 columns and the same row counts listed above. The restore role is not superuser and has no CREATEROLE/BYPASSRLS; its CREATE privileges are confined to the isolated restore database. A read-only query against Production `br-damp-fog-bi0lzjf4` afterward returned the unchanged counts: users=0, audit_events=2, auth_attempts=4, auth_sessions=0, platform_state=1. Production was not used as the restore target. A second offline recovery copy of the private key remains outstanding.


## Current Production migration-role evidence — 2026-11-27

- `nanou_migration_login` successfully executed `SET LOCAL ROLE nanou_migration_owner` in a read-only Production transaction. The login role has no elevated attributes or direct public-schema CREATE; the effective NOLOGIN owner has public-schema CREATE and no elevated role flags.
- Owner-role default ACLs are present for future tables/sequences: runtime receives table DML and sequence SELECT/USAGE; backup receives SELECT only.
- All 9 current Production tables and the database remain owned by `nanou_app`. Runtime/backup aggregate grants are least-privilege as described above. No ownership transfer, production DDL, grant change, credential revocation or deployment was performed.
- The full database/table/sequence ownership transfer, post-transfer smoke test and rollback window remain to be rehearsed on a suitable isolated copy before Production cutover.
