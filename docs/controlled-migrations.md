# Controlled PostgreSQL migrations

The FastAPI runtime must use only \`NANOU_RUNTIME_DATABASE_URL\`, backed by
\`nanou_preview_runtime\` in Preview. It must never invoke this command or
receive migration credentials.

## Current safety boundary

- The intended Preview migration login is \`nanou_preview_migration_login\`;
  schema changes require \`SET ROLE nanou_preview_migration_owner\`.
- The runner uses a transaction-scoped advisory lock and applies pending SQL
  files and their ledger entries in one transaction.
- Each applied migration has an immutable SHA-256 checksum. A changed checksum
  for an applied version blocks the run.
- Migration filenames use \`NNNN_description.sql\`; empty, malformed, duplicate
  and symlinked files are rejected.
- Dry-run listing is the default. Applying requires \`--apply\`,
  \`NANOU_MIGRATION_DATABASE_URL\`, and an explicit \`NANOU_MIGRATION_TARGET\`.
- Production is hard-blocked. Execution is pinned in code to the isolated
  Neon Preview endpoint and database \`nanou_preview\`; changing this allowlist
  requires a reviewed code change.
- The runner requires TLS and verifies both migration roles' PostgreSQL
  attributes: login role has LOGIN but no elevated flags; owner role is NOLOGIN
  with no elevated flags.
- The Preview audit found \`nanou_preview_app\` owns the existing application
  tables and sequences. \`nanou_preview_owner\` is overprivileged and a member
  of \`neon_superuser\`; do not use it as the migration login.
- The required \`nanou_preview_migration_login\` and
  \`nanou_preview_migration_owner\` roles are not yet provisioned. Apply remains
  blocked until they are created and least-privilege grants/default privileges
  are verified on Preview.
- The runner does not generate DDL from SQLAlchemy metadata and does not
  automatically baseline an existing database. No migration SQL is included.

## Preview dry run

\`\`\`bash
export NANOU_MIGRATION_TARGET=preview
python scripts/db_migrate.py
\`\`\`

This only lists migration names and checksums; it does not connect to Neon.

## Preview apply — currently blocked pending role provisioning

Do not run with \`--apply\` until the dedicated Preview migration roles exist
and their login, membership, schema DDL, table/sequence ownership and default
privileges have been verified. Do not substitute \`nanou_preview_app\`,
\`nanou_preview_owner\` or \`nanou_preview_runtime\`.

After that prerequisite, provide the dedicated Preview migration login URL
through the protected \`NANOU_MIGRATION_DATABASE_URL\` environment variable
and run:

\`\`\`bash
python scripts/db_migrate.py --apply
\`\`\`

Never put database URLs in shell history, command arguments, CI output, logs,
Git, screenshots or chat. Never reuse a Production database URL in Preview.

## Before Production support can be enabled

A separate code change and explicit approval are required. It must include a
fresh backup/restore verification, tested forward and rollback SQL, a
maintenance window, a reviewed migration diff, Production-specific role and
credential verification, a tested recovery path, and post-migration
application acceptance tests.
