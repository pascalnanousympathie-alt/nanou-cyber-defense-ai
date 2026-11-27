-- Google account identifiers are keyed by Google's immutable OIDC `sub` claim.
-- Apply with the reviewed migration database role before deploying code that
-- expects this table. Do not auto-run DDL from the serverless application role.
BEGIN;
SET LOCAL ROLE nanou_migration_owner;

CREATE TABLE IF NOT EXISTS public.google_identities (
    google_subject VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(32) NOT NULL UNIQUE
        REFERENCES public.users (id) ON DELETE CASCADE,
    email_at_link VARCHAR(320) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMIT;
