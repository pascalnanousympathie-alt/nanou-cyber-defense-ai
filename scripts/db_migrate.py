"""Apply reviewed PostgreSQL migrations using a dedicated, least-privilege owner role.

This command is separate from the FastAPI runtime. Production execution is
intentionally disabled; only the pinned isolated Neon Preview database is allowed.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import psycopg

MIGRATION_DIR = Path(__file__).resolve().parents[1] / "migrations"
LEDGER_TABLE = "public.nanou_schema_migrations"
MIGRATION_ROLE = "nanou_migration_owner"
MIGRATION_LOGIN = "nanou_migration_login"
VERSION_PATTERN = re.compile(r"^(?P<version>[0-9]{4,})_[a-z0-9_]+\.sql$")
LOCK_KEY = 741_902_611
PREVIEW_ALLOWED_HOST = "ep-bitter-sunset-biteo9x5.c-5.ap-southeast-1.aws.neon.tech"
PREVIEW_ALLOWED_DATABASE = "nanou_preview"


@dataclass(frozen=True)
class Migration:
    version: str
    name: str
    path: Path
    checksum: str
    sql: str


class MigrationError(RuntimeError):
    """Raised when migration safety or consistency checks fail."""


def load_migrations(directory: Path = MIGRATION_DIR) -> list[Migration]:
    """Load ordered SQL migrations and reject ambiguous or empty files."""
    if not directory.exists():
        return []
    migrations: list[Migration] = []
    seen_versions: set[str] = set()
    for path in sorted(directory.glob("*.sql")):
        if path.is_symlink():
            raise MigrationError(f"Migration must not be a symlink: {path.name}")
        match = VERSION_PATTERN.fullmatch(path.name)
        if match is None:
            raise MigrationError(f"Invalid migration filename: {path.name}")
        version = match.group("version")
        if version in seen_versions:
            raise MigrationError(f"Duplicate migration version: {version}")
        seen_versions.add(version)
        sql = path.read_text(encoding="utf-8").strip()
        if not sql:
            raise MigrationError(f"Migration is empty: {path.name}")
        checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
        migrations.append(Migration(version, path.name, path, checksum, sql))
    return migrations


def validate_target(target: str | None) -> str:
    """Require an explicit non-Production target; Production is hard-blocked."""
    if target not in {"development", "preview", "production"}:
        raise MigrationError(
            "Set NANOU_MIGRATION_TARGET to development or preview explicitly."
        )
    if target == "production":
        raise MigrationError(
            "Production migrations are disabled; use the separately approved "
            "Production change procedure."
        )
    return target


def validate_database_target(database_url: str, target: str) -> None:
    """Pin executable migrations to the known isolated Neon Preview database."""
    validate_target(target)
    parsed = urlsplit(database_url)
    database_name = parsed.path.lstrip("/")
    if (
        target != "preview"
        or parsed.hostname != PREVIEW_ALLOWED_HOST
        or database_name != PREVIEW_ALLOWED_DATABASE
    ):
        raise MigrationError(
            "Migration execution is restricted to the approved isolated Preview database."
        )


def validate_session_roles(effective_role: str, login_role: str) -> None:
    """Require the dedicated migration login and its NOLOGIN owner role."""
    if effective_role != MIGRATION_ROLE or login_role != MIGRATION_LOGIN:
        raise MigrationError(
            "Database session must be nanou_migration_login with "
            "SET ROLE nanou_migration_owner."
        )


def validate_role_flags(flags: Sequence[bool]) -> None:
    """Require a non-privileged LOGIN and a non-LOGIN migration owner."""
    if len(flags) != 12:
        raise MigrationError("Could not verify migration role attributes.")
    login_can_login = flags[0]
    login_privileges = flags[1:6]
    owner_can_login = flags[6]
    owner_privileges = flags[7:12]
    if (
        not login_can_login
        or any(login_privileges)
        or owner_can_login
        or any(owner_privileges)
    ):
        raise MigrationError("Migration login/owner roles have unsafe PostgreSQL attributes.")


def apply_migrations(
    database_url: str,
    target: str,
    migrations: Sequence[Migration],
) -> list[str]:
    """Apply pending migrations atomically under the migration owner role."""
    validate_database_target(database_url, target)
    if not database_url.startswith(("postgresql://", "postgres://")):
        raise MigrationError("Migration URL must use PostgreSQL.")

    applied: list[str] = []
    with psycopg.connect(database_url, connect_timeout=10) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SET ROLE nanou_migration_owner")
            cursor.execute("SELECT current_user, session_user, current_database()")
            effective_role, login_role, database_name = cursor.fetchone()
            validate_session_roles(effective_role, login_role)
            if database_name != PREVIEW_ALLOWED_DATABASE:
                raise MigrationError(
                    "Connected database is not the approved isolated Preview database."
                )

            cursor.execute(
                """
                SELECT login.rolcanlogin, login.rolsuper, login.rolcreatedb,
                       login.rolcreaterole, login.rolreplication, login.rolbypassrls,
                       owner.rolcanlogin, owner.rolsuper, owner.rolcreatedb,
                       owner.rolcreaterole, owner.rolreplication, owner.rolbypassrls
                FROM pg_roles AS login
                CROSS JOIN pg_roles AS owner
                WHERE login.rolname = %s AND owner.rolname = %s
                """,
                (MIGRATION_LOGIN, MIGRATION_ROLE),
            )
            role_flags = cursor.fetchone()
            if role_flags is None:
                raise MigrationError("Dedicated migration roles are not provisioned.")
            validate_role_flags(role_flags)

            cursor.execute("SELECT pg_advisory_xact_lock(%s)", (LOCK_KEY,))
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {LEDGER_TABLE} (
                    version text PRIMARY KEY,
                    name text NOT NULL,
                    checksum char(64) NOT NULL,
                    applied_at timestamptz NOT NULL DEFAULT now()
                )
                """
            )
            cursor.execute(
                f"SELECT version, checksum FROM {LEDGER_TABLE} ORDER BY version"
            )
            existing = dict(cursor.fetchall())

            for migration in migrations:
                previous_checksum = existing.get(migration.version)
                if previous_checksum is not None:
                    if previous_checksum.strip() != migration.checksum:
                        raise MigrationError(
                            f"Applied migration checksum changed: {migration.name}"
                        )
                    continue

                cursor.execute(migration.sql)
                cursor.execute(
                    f"""
                    INSERT INTO {LEDGER_TABLE} (version, name, checksum)
                    VALUES (%s, %s, %s)
                    """,
                    (migration.version, migration.name, migration.checksum),
                )
                applied.append(migration.name)

    return applied


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply pending migrations (default is a local dry-run listing).",
    )
    args = parser.parse_args(argv)

    try:
        target = validate_target(os.getenv("NANOU_MIGRATION_TARGET"))
        migrations = load_migrations()
        if not migrations:
            print(f"Target: {target}; no SQL migrations found.")
            return 0

        for migration in migrations:
            print(f"{migration.version} {migration.name} sha256={migration.checksum}")

        if not args.apply:
            print(f"Dry run only; {len(migrations)} migration(s) inspected, none applied.")
            return 0

        database_url = os.getenv("NANOU_MIGRATION_DATABASE_URL")
        if not database_url:
            raise MigrationError(
                "NANOU_MIGRATION_DATABASE_URL is required with --apply."
            )

        applied = apply_migrations(database_url, target, migrations)
        print(f"Applied {len(applied)} migration(s) to {target}.")
        return 0
    except psycopg.Error:
        print(
            "Migration blocked: database operation failed; details omitted to protect credentials.",
            file=sys.stderr,
        )
        return 2
    except (MigrationError, OSError) as exc:
        print(f"Migration blocked: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
