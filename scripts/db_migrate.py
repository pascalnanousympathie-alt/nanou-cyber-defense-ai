"""Apply reviewed, versioned PostgreSQL migrations with a dedicated owner role.

The application runtime must never invoke this module. Production execution is
intentionally disabled until a separate, explicitly reviewed change enables it.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import psycopg

MIGRATION_DIR = Path(__file__).resolve().parents[1] / "migrations"
LEDGER_TABLE = "public.nanou_schema_migrations"
MIGRATION_ROLE = "nanou_migration_owner"
VERSION_PATTERN = re.compile(r"^(?P<version>[0-9]{4,})_[a-z0-9_]+\.sql$")
LOCK_KEY = 741_902_611


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
            "Production migrations are disabled by this runner; use the separately "
            "approved Production change procedure."
        )
    return target


def apply_migrations(
    database_url: str,
    target: str,
    migrations: Sequence[Migration],
) -> list[str]:
    """Apply all pending migrations atomically under the migration owner role."""
    validate_target(target)
    if not database_url.startswith(("postgresql://", "postgres://")):
        raise MigrationError("Migration URL must use PostgreSQL.")
    applied: list[str] = []
    with psycopg.connect(database_url, connect_timeout=10) as connection:
        with connection.cursor() as cursor:
            cursor.execute(f"SET ROLE {MIGRATION_ROLE}")
            cursor.execute("SELECT current_user, session_user")
            effective_role, login_role = cursor.fetchone()
            if effective_role != MIGRATION_ROLE or login_role == MIGRATION_ROLE:
                raise MigrationError("Database session did not assume the migration owner role.")
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
            raise MigrationError("NANOU_MIGRATION_DATABASE_URL is required with --apply.")
        applied = apply_migrations(database_url, target, migrations)
        print(f"Applied {len(applied)} migration(s) to {target}.")
        return 0
    except (MigrationError, OSError, psycopg.Error) as exc:
        print(f"Migration blocked: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
