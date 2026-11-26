# Controlled PostgreSQL migrations

The FastAPI runtime must use only `NANOU_RUNTIME_DATABASE_URL`. It must never
run this migration command or receive migration credentials.

## Current safety boundary

- The migration login is expected to be `nanou_migration_login`, with
  `SET ROLE nanou_migration_owner` required for schema changes.
- The runner uses an advisory transaction lock and applies pending SQL files
  plus their ledger entries in one database transaction.
- Each migration is immutable after application: its SHA-256 checksum is
  stored and verified on subsequent runs.
- Migration filenames must be `NNNN_description.sql`, sorted lexically.
- The default is a dry-run listing. Applying requires an explicit
  `--apply`, `NANOU_MIGRATION_DATABASE_URL`, and an explicit
  `NANOU_MIGRATION_TARGET`.
- `production` is deliberately rejected in this implementation. There is no
  flag or environment override to bypass this guard.
- No migration SQL is supplied by this runner. Schema changes must be authored,
  reviewed and tested separately; it does not generate DDL from SQLAlchemy
  metadata or attempt to baseline an existing database automatically.

## Local / Preview usage

Install the project dependencies, then set the target explicitly:

```bash
export NANOU_MIGRATION_TARGET=preview
python scripts/db_migrate.py
```

The command lists checksums only and does not connect to the database.

For a reviewed migration on an isolated Preview database, provide its dedicated
migration login URL through the secret environment variable and run:

```bash
python scripts/db_migrate.py --apply
```

Do not put the URL in shell history, command arguments, CI output, logs, Git,
screenshots or chat. Prefer a short-lived CI secret or a local protected
environment variable. Never reuse the Production migration URL in Preview.

## Before Production support can be enabled

A separate change and explicit approval are required. It must include a fresh
backup/restore verification, tested forward and rollback SQL, a maintenance
window, a reviewed migration diff, a Production-specific credential check,
a tested recovery path, and a post-migration application acceptance test.
