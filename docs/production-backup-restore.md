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

**Current status: CONFIGURED / NOT ACTIVE.** The repository Actions secret `NANOU_BACKUP_DATABASE_URL` is now provisioned; its name was verified through `gh secret list` without displaying or transferring its value. The workflow file is currently on this PR branch only, and the job has a hard guard requiring `refs/heads/main`. Therefore no Production dump runs from this PR. The scheduled/manual backup remains inactive until this PR is explicitly approved and merged to `main`. No encrypted Production artifact or automated restore rehearsal is claimed. Never place the connection URI in source code, logs, or chat.

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
- The latest workflow refinement explicitly verifies public-schema USAGE, SELECT on every public sequence, and absence of RLS/FORCE RLS on public tables before dumping. This refinement was committed after the last successful CI/security run and still requires exact-head CI/security validation.
- The crypto tests use an ephemeral RSA keypair to prove streaming round-trip, authentication-tag tamper rejection, and rejection of RSA keys below 3072 bits. This is cryptographic unit-test evidence only; it is not an actual Production artifact restore rehearsal.
- The last validated CI run [45827291114](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45827291114) produced no backup artifacts. Production snapshot evidence remains the manual snapshot `snap-shiny-fire-bir6x6kk`; no scheduled GitHub backup artifact has been produced. The scheduled workflow is restricted to `main`, and the repository Actions secret `NANOU_BACKUP_DATABASE_URL` still requires owner provisioning through GitHub Settings.
- The matching offline private key path is documented above. Its current file existence/permissions and the presence of a second offline recovery copy were not re-verified in this session because both Desktop Commander devices checked (Nanou48 and Mercia) were offline. Verify the key locally without displaying or transferring its contents before relying on encrypted backups for recovery.
- Production remains on Vercel deployment commit `db4fa6a7c059467b8728468425d63ce78414ef5d`; Production `/api/auth/me` previously reported `bootstrap_required=true`. Production database ownership remains with `nanou_app`. No Admin bootstrap, ownership transfer, merge, Production deployment, or credential revocation was performed.
- Neon rejected protecting Production branch `main` with HTTP 422 because the current plan's protected-branch quota is full. No other branch protection was removed and no paid upgrade was made.


## Current verification — 2026-11-26

- Exact PR head: `2458f8bba97a762478a426c14f150ecd3a048871`.
- CI run [45829753859](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45829753859): PASS — Ruff lint/format; 51 passed / 4 skipped; ML smoke 13 passed; pip-audit found no known vulnerabilities.
- Security run [45829753884](https://github.com/pascalnanousympathie-alt/nanou-cyber-defense-ai/actions/runs/45829753884): PASS — Gitleaks found no leaks; CodeQL Python succeeded; JavaScript/TypeScript was explicitly not applicable because this ref contains no non-empty tracked JS/TS source files.
- GitHub Actions secret `NANOU_BACKUP_DATABASE_URL`: present (secret name verified; secret value not printed).
- On Desktop Commander device Nanou, the local private key exists with mode `600`; its derived public-key SHA-256 fingerprint matches the pinned recipient fingerprint `f5cb681b49a315ee94dccf420fdef26b92ac002c723f85544a0b5dd77b6fa7c1`. A separate offline recovery copy has not yet been verified.
- The workflow is restricted to `refs/heads/main`; the PR remains open/draft and unmerged. No scheduled/manual Production backup has run, no encrypted Production artifact exists yet, and no automated artifact restore rehearsal has been completed.
