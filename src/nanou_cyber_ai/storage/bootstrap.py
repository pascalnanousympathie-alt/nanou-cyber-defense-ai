"""One-time PostgreSQL schema bootstrap using a dedicated migration credential.

The web application must not run DDL at startup. This command is for the initial
schema only; future schema evolution must use separately reviewed migrations.
"""

from __future__ import annotations

import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert as pg_insert

from nanou_cyber_ai.storage.database import metadata, platform_state


def normalize_postgres_url(value: str) -> str:
    """Validate and normalize a PostgreSQL URL without exposing it in errors."""
    url = value.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    if not url.startswith("postgresql+psycopg://"):
        raise ValueError("NANOU_MIGRATION_DATABASE_URL must use PostgreSQL.")
    return url


def bootstrap_schema(database_url: str) -> None:
    """Create missing initial tables and bootstrap state using migration privileges."""
    normalized_url = normalize_postgres_url(database_url)
    engine = create_engine(
        normalized_url,
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
        connect_args={"sslmode": "require", "prepare_threshold": None},
    )
    try:
        metadata.create_all(engine)
        with engine.begin() as connection:
            connection.execute(
                pg_insert(platform_state)
                .values(id=1, bootstrap_claimed=False)
                .on_conflict_do_nothing(index_elements=[platform_state.c.id])
            )
    finally:
        engine.dispose()


def main() -> int:
    """Read the migration URL from the environment; never print the secret."""
    database_url = os.environ.get("NANOU_MIGRATION_DATABASE_URL")
    if not database_url:
        print("NANOU_MIGRATION_DATABASE_URL is required.", file=sys.stderr)
        return 2
    try:
        bootstrap_schema(database_url)
    except (ValueError, OSError) as exc:
        print(f"PostgreSQL schema bootstrap failed: {exc}", file=sys.stderr)
        return 1
    print("Initial PostgreSQL schema bootstrap completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
