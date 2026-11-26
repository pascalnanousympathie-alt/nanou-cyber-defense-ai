# Production backup and restore

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
- Restore branch is an isolated drill copy. It has since been used to validate NOLOGIN ownership, separate migration login, DML runtime privileges and default grants. It is not Production.

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

- Runs daily at 02:17 UTC or via manual dispatch, only from `main`.
- Uses the read-only `nanou_backup` connection.
- Runs PostgreSQL 17 `pg_dump --format=custom --no-owner --no-privileges`, validates with `pg_restore --list`, encrypts the dump, writes SHA-256 and a manifest, then uploads only the encrypted artifact.
- GitHub artifact retention is 30 days.
- The workflow requires repository Actions secret `NANOU_BACKUP_DATABASE_URL`; it must contain the direct-host PostgreSQL URL for `nanou_backup`, not the runtime or owner credential.

**Current status: FIRST BACKUP COMPLETED; SCHEDULE ACTIVE.** The repository Actions secret `NANOU_BACKUP_DATABASE_URL` is provisioned. PR #5 merged the workflow to `main`; its hard guard requires `refs/heads/main`. The first manual Production backup completed successfully on 2026-11-26 and its encrypted artifact is retained for 30 days. Daily schedule is enabled. An authenticated decrypt-and-restore rehearsal of this downloaded artifact is still outstanding. Never place the connection URI in source code, logs, or chat.

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
- Production database ownership remains with `nanou_app`; the old Vercel Production deployment at `db4fa6a7c059467b8728468425d63ce78414ef5d` remains the last READY Production deployment. A new Production build on the backup-workflow merge commit failed with `FASTAPI_ENTRYPOINT_NOT_FOUND`; PR #6 adds the recommended `[tool.vercel] entrypoint` configuration. Its Preview build is READY, but the fix has not been merged to `main` or promoted to Production. No Admin bootstrap, ownership transfer, or credential revocation was performed.
- Neon rejected protecting Production branch `main` with HTTP 422 because the current plan's protected-branch quota is full. No other branch protection was removed and no paid upgrade was made.


## Current verification — 2026-11-26

- Exact PR head: `2458f8bba97a762478a426c14f150ecd3a048871`.
- CI run [45829753859](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45829753859): PASS — Ruff lint/format; 51 passed / 4 skipped; ML smoke 13 passed; pip-audit found no known vulnerabilities.
- Security run [45829753884](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45829753884): PASS — Gitleaks found no leaks; CodeQL Python succeeded; JavaScript/TypeScript was explicitly not applicable because this ref contains no non-empty tracked JS/TS source files.
- GitHub Actions secret `NANOU_BACKUP_DATABASE_URL`: present (secret name verified; secret value not printed).
- On Desktop Commander device Nanou, the local private key exists with mode `600`; its derived public-key SHA-256 fingerprint matches the pinned recipient fingerprint `f5cb681b49a315ee94dccf420fdef26b92ac002c723f85544a0b5dd77b6fa7c1`. A separate offline recovery copy has not yet been verified.
- The workflow remains restricted to `refs/heads/main`. PR #5 is merged; the manual workflow_dispatch run `45850155507` succeeded, and one encrypted artifact exists. No post-download authenticated decrypt-and-restore rehearsal has been completed.


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
- The same missing Vercel configuration was present in the parent `main` commit before PR #5, so this is a pre-existing project configuration defect, not a backup workflow failure.
- The previous Vercel Production deployment at `db4fa6a7c059467b8728468425d63ce78414ef5d` remains READY. The PR #6 Preview for head `e9430b037bdd77fa425459bede296452057e65b7` is READY (`dpl_89tdV6FXpuKZUhMDUEqN8ZWb52Mw`). The preview is protected by Vercel Authentication, so unauthenticated `/health` and `/openapi.json` checks were not completed. No Production promotion or deployment was performed.


## PR #6 validation — 2026-11-26

- PR: [#6 — Fix Vercel FastAPI entrypoint and portable backup checksum](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/pull/6).
- At validated head `e9430b037bdd77fa425459bede296452057e65b7`, CI run [45851810022](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45851810022) passed: Ruff lint/format; 51 tests passed / 4 skipped; ML smoke 13 passed; dependency audit found no known vulnerabilities.
- Security run [45851809676](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45851809676) passed: Gitleaks, CodeQL Python and CodeQL JavaScript/TypeScript.
- Vercel generated a Preview deployment for the PR branch; deployment `dpl_89tdV6FXpuKZUhMDUEqN8ZWb52Mw` reached **READY** with the FastAPI entrypoint configured. This is Preview only, not a Production promotion. HTTP endpoint verification remained blocked by Vercel Authentication.
- The revised relative checksum command was exercised with a synthetic test payload on the authorized Termux device; `sha256sum -c` returned `OK`. The next actual Production backup should verify the new sidecar format on the uploaded artifact.
- PR #6 remains open and unmerged. Merge would trigger the connected Vercel Production deployment; do not merge or promote without explicit Production approval.
