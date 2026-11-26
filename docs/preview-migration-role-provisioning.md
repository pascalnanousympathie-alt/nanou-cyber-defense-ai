# Preview migration-role provisioning plan

This is a reviewed plan only. It has **not** been executed. It is scoped to
Neon project \`young-snow-19049684\`, branch \`br-long-field-bianlzu3\`,
database \`nanou_preview\`. Do not run it against Production.

## Current Preview findings

- \`nanou_preview_app\` owns the 9 application tables and 2 sequences.
- \`nanou_preview_runtime\` has DML on the 9 tables, sequence USAGE/SELECT,
  no TRUNCATE/sequence UPDATE, and no schema CREATE.
- Default privileges for both current object creators grant the same DML and
  sequence access to \`nanou_preview_runtime\`.
- \`nanou_preview_owner\` is overprivileged and a member of
  \`neon_superuser\`; do not use it for migration execution.
- The dedicated migration roles below do not yet exist.

## Intended role model

Create two separate roles:

- \`nanou_preview_migration_owner\`: NOLOGIN, NOSUPERUSER, NOCREATEDB,
  NOCREATEROLE, NOREPLICATION, NOBYPASSRLS. It owns schema objects and has
  USAGE/CREATE on schema \`public\`, but no database CREATE.
- \`nanou_preview_migration_login\`: LOGIN, NOSUPERUSER, NOCREATEDB,
  NOCREATEROLE, NOREPLICATION, NOBYPASSRLS. Its password must be generated
  and stored using the Neon Console's protected role/credential workflow.
  Do not paste it into SQL, Git, CI logs, screenshots or chat.

Grant membership with SET ROLE but no inherited owner privileges:

\`\`\`sql
GRANT nanou_preview_migration_owner
TO nanou_preview_migration_login
WITH INHERIT FALSE, SET TRUE;

GRANT USAGE, CREATE ON SCHEMA public
TO nanou_preview_migration_owner;
\`\`\`

## Ownership transfer plan

Only after both roles have been created and inspected, transfer the 9 tables
and 2 sequences in one transaction on the Preview branch:

\`\`\`sql
BEGIN;

ALTER TABLE public.api_keys OWNER TO nanou_preview_migration_owner;
ALTER TABLE public.attack_scopes OWNER TO nanou_preview_migration_owner;
ALTER TABLE public.attack_simulations OWNER TO nanou_preview_migration_owner;
ALTER TABLE public.audit_events OWNER TO nanou_preview_migration_owner;
ALTER TABLE public.auth_attempts OWNER TO nanou_preview_migration_owner;
ALTER TABLE public.auth_sessions OWNER TO nanou_preview_migration_owner;
ALTER TABLE public.malware_metadata OWNER TO nanou_preview_migration_owner;
ALTER TABLE public.platform_state OWNER TO nanou_preview_migration_owner;
ALTER TABLE public.users OWNER TO nanou_preview_migration_owner;

ALTER SEQUENCE public.auth_attempts_id_seq OWNER TO nanou_preview_migration_owner;
ALTER SEQUENCE public.platform_state_id_seq OWNER TO nanou_preview_migration_owner;

ALTER DEFAULT PRIVILEGES FOR ROLE nanou_preview_migration_owner IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO nanou_preview_runtime;

ALTER DEFAULT PRIVILEGES FOR ROLE nanou_preview_migration_owner IN SCHEMA public
GRANT USAGE, SELECT ON SEQUENCES TO nanou_preview_runtime;

COMMIT;
\`\`\`

## Required post-change checks

- All 11 existing objects are owned by \`nanou_preview_migration_owner\`.
- The migration login can \`SET ROLE nanou_preview_migration_owner\`.
- The login and owner roles have no superuser, CREATEDB, CREATEROLE,
  replication or BYPASSRLS attributes.
- The migration login has no inherited schema/table/sequence privileges
  outside the owner role.
- Runtime retains SELECT/INSERT/UPDATE/DELETE on all 9 tables, USAGE/SELECT
  on both sequences, and still lacks TRUNCATE, sequence UPDATE and schema CREATE.
- New tables and sequences created under the owner role grant only the expected
  runtime privileges.
- Row counts and ordered row digests match the pre-change Preview baseline.
- A disposable table test proves migration DDL and runtime CRUD, then removes
  the disposable table and rechecks object counts.

Do not execute until explicitly approved. The migration runner remains blocked
until this role setup is completed and independently verified.
