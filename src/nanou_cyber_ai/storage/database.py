"""Shared SQLite/PostgreSQL storage for the web platform.

SQLite is intentionally limited to local development and tests. Hosted
serverless deployments must configure NANOU_DATABASE_URL for durable storage.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    event,
    func,
    insert,
)
from sqlalchemy.exc import IntegrityError

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", String(32), primary_key=True),
    Column("email", String(320), nullable=False, unique=True),
    Column("display_name", String(100), nullable=False),
    Column("password_hash", String(255), nullable=False),
    Column("role", String(16), nullable=False, server_default="viewer"),
    Column("is_approved", Boolean, nullable=False, server_default="false"),
    Column("is_active", Boolean, nullable=False, server_default="false"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

sessions = Table(
    "auth_sessions",
    metadata,
    Column("token_hash", String(64), primary_key=True),
    Column("user_id", String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("last_seen_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("expires_at", DateTime(timezone=True), nullable=False),
)
Index("ix_auth_sessions_user", sessions.c.user_id)
Index("ix_auth_sessions_expiry", sessions.c.expires_at)

api_keys = Table(
    "api_keys",
    metadata,
    Column("id", String(32), primary_key=True),
    Column("owner_user_id", String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("name", String(80), nullable=False),
    Column("token_prefix", String(24), nullable=False),
    Column("token_hash", String(64), nullable=False, unique=True),
    Column("scopes", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("last_used_at", DateTime(timezone=True)),
    Column("revoked_at", DateTime(timezone=True)),
    Column("rate_window_started_at", DateTime(timezone=True)),
    Column("request_count", Integer, nullable=False, server_default="0"),
)
Index("ix_api_keys_owner", api_keys.c.owner_user_id)
Index("ix_api_keys_expiry", api_keys.c.expires_at)

audit_events = Table(
    "audit_events",
    metadata,
    Column("id", String(32), primary_key=True),
    Column("actor_user_id", String(32), ForeignKey("users.id", ondelete="SET NULL")),
    Column("action", String(100), nullable=False),
    Column("target_type", String(80), nullable=False),
    Column("target_id", String(100)),
    Column("outcome", String(24), nullable=False),
    Column("request_id", String(80)),
    Column("ip_digest", String(64)),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
Index("ix_audit_events_created", audit_events.c.created_at)
Index("ix_audit_events_actor", audit_events.c.actor_user_id)

auth_attempts = Table(
    "auth_attempts",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("fingerprint", String(64), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
Index("ix_auth_attempts_fingerprint", auth_attempts.c.fingerprint)
Index("ix_auth_attempts_created", auth_attempts.c.created_at)

platform_state = Table(
    "platform_state",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("bootstrap_claimed", Boolean, nullable=False, server_default="false"),
)

malware_metadata = Table(
    "malware_metadata",
    metadata,
    Column("sha256", String(64), primary_key=True),
    Column("payload_json", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)


class SecurityDatabase:
    """A small connection-per-operation database facade."""

    def __init__(self, database_url: str | None, data_dir: Path) -> None:
        if database_url:
            normalized_url = database_url.strip()
            if normalized_url.startswith("postgres://"):
                normalized_url = normalized_url.replace("postgres://", "postgresql+psycopg://", 1)
            elif normalized_url.startswith("postgresql://"):
                normalized_url = normalized_url.replace("postgresql://", "postgresql+psycopg://", 1)
            if not normalized_url.startswith("postgresql+psycopg://"):
                raise ValueError("NANOU_DATABASE_URL must use PostgreSQL.")
            self.mode = "postgresql"
            self.engine = create_engine(
                normalized_url,
                pool_pre_ping=True,
                pool_size=1,
                max_overflow=0,
                pool_recycle=300,
                connect_args={"sslmode": "require", "prepare_threshold": None},
            )
        else:
            import os

            if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
                raise RuntimeError(
                    "A durable NANOU_DATABASE_URL is required on serverless hosting."
                )
            data_dir = data_dir.expanduser()
            data_dir.mkdir(parents=True, exist_ok=True)
            database_path = data_dir / "malware_metadata.sqlite3"
            self.mode = "sqlite"
            self.engine = create_engine(
                f"sqlite:///{database_path}",
                connect_args={"check_same_thread": False, "timeout": 15},
                pool_pre_ping=True,
            )
            event.listen(self.engine, "connect", self._enable_sqlite_foreign_keys)

        metadata.create_all(self.engine)
        self._ensure_bootstrap_state()

    @staticmethod
    def _enable_sqlite_foreign_keys(connection, _record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    def _ensure_bootstrap_state(self) -> None:
        try:
            with self.engine.begin() as connection:
                connection.execute(insert(platform_state).values(id=1, bootstrap_claimed=False))
        except IntegrityError:
            # The row already exists; a concurrent cold start may have inserted it.
            pass

    def close(self) -> None:
        self.engine.dispose()


@lru_cache(maxsize=8)
def _cached_database(database_url: str | None, data_dir: str) -> SecurityDatabase:
    return SecurityDatabase(database_url, Path(data_dir))


def get_database(database_url: str | None, data_dir: Path) -> SecurityDatabase:
    """Get a cached engine without retaining a readable copy of a secret in logs."""
    return _cached_database(database_url, str(data_dir.expanduser()))
