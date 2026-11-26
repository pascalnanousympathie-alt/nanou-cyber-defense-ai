# Controlled PostgreSQL migrations

The FastAPI runtime must use only `NANOU_RUNTIME_DATABASE_URL`. It must never
invoke this command or receive migration credentials.

## Current safety boundary

- The expected login is `nanou_migration_login`; schema changes require
  `SET ROLE nanou_migration_owner`.
- The runner uses a transaction-scoped advisory lock and applies pending SQL
  files and their ledger entries in one transaction.
- Each applied migration has an immutable SHA-256 checksum. A changed checksum
  for an applied version blocks the run.
- Migration filenames use `NNNN_description.sql`; empty, malformed, duplicate
  and symlinked files are rejected.
- Dry-run listing is the default. Applying requires `--apply`,
  `NANOU_MIGRATION_DATABASE_URL`, and an explicit `NANOU_MIGRATION_TARGET`.
- Production is hard-blocked. The executable path is pinned in code to the
  isolated Neon Preview endpoint and database `nanou_preview`; changing this
  allowlist requires a reviewed code change.
- The runner does not generate DDL from SQLAlchemy metadata and does not
  automatically baseline an existing database. No migration SQL is included.

## Preview dry run

```bash
export NANOU_MIGRATION_TARGET=preview
python scripts/db_migrate.py
```

This only lists migration names and checksums; it does not connect to Neon.

## Preview apply — currently blocked pending role provisioning

The current Preview branch audit identified database `nanou_preview`, but
`nanou_migration_login` and `nanou_migration_owner` were not present in
`pg_roles`. Therefore do not run with `--apply` until those roles and their
least-privilege grants are separately provisioned and verified on Preview.
Do not substitute the app or runtime login.

After that prerequisite, provide the dedicated Preview migration login URL
through the protected `NANOU_MIGRATION_DATABASE_URL` environment variable
and run:

```bash
python scripts/db_migrate.py --apply
```

Never put database URLs in shell history, command arguments, CI output, logs,
Git, screenshots or chat. Never reuse a Production database URL in Preview.

## Before Production support can be enabled

A separate code change and explicit approval are required. It must include a
fresh backup/restore verification, tested forward and rollback SQL, a
maintenance window, a reviewed migration diff, Production-specific role and
credential verification, a tested recovery path, and post-migration
application acceptance tests.
