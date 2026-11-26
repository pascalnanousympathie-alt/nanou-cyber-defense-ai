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

**Current status: BLOCKED / NOT ACTIVE.** The workflow and crypto code are committed to this PR branch, but `NANOU_BACKUP_DATABASE_URL` has not been provisioned as a GitHub Actions secret. No unencrypted dump was uploaded. The automated schedule will not run until the workflow is merged to `main` and the secret is available. The connector route for setting this secret was unavailable, and the attempted secret handoff was stopped by the security guard; do not bypass that guard or put the credential in source code.

## Production cutover gates

1. Confirm the current Production app has deployed code that selects `NANOU_RUNTIME_DATABASE_URL` and fails closed when it is absent.
2. Confirm the exact Production runtime URL with the `nanou_runtime` role and run read-only health plus disposable DML smoke tests.
3. Confirm a fresh backup exists and decrypt/restore it in an isolated destination.
4. Transfer database/tables/sequences to the NOLOGIN `nanou_migration_owner`; establish default grants for `nanou_runtime` and `nanou_backup`.
5. Verify login `nanou_migration_login` can only perform reviewed DDL after `SET ROLE nanou_migration_owner`.
6. Deploy and smoke-test the exact production candidate; then retire the old `nanou_app` credential only after the rollback window is closed.
7. Preserve Vercel SSO and retain a documented recovery path.

No Production ownership transfer, old-role deletion, merge to `main`, or Production deployment is performed by this runbook alone.
