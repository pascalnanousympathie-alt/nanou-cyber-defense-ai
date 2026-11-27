"""Shared SQLite/PostgreSQL storage for the web platform.

SQLite is intentionally limited to local development and tests. Hosted
serverless deployments must configure NANOU_RUNTIME_DATABASE_URL for durable storage.
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
    inspect,
)
from sqlalchemy.exc import IntegrityError

metadata = MetaData()
# Optional Google identity storage has a separately reviewed PostgreSQL migration.
# Keeping it outside the mandatory runtime schema lets password auth remain live
# until the migration is safely applied to a hosted database.
google_metadata = MetaData()

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

users.to_metadata(google_metadata)
google_identities = Table(
    "google_identities",
    google_metadata,
    Column("google_subject", String(255), primary_key=True),
    Column(
        "user_id",
        String(32),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    ),
    Column("email_at_link", String(320), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)

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

attack_scopes = Table(
    "attack_scopes",
    metadata,
    Column("id", String(32), primary_key=True),
    Column(
        "created_by_user_id",
        String(32),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    ),
    Column("name", String(80), nullable=False),
    Column("target", String(253), nullable=False),
    Column("target_type", String(12), nullable=False),
    Column("authorization_basis", String(32), nullable=False),
    Column("authorization_expires_at", DateTime(timezone=True), nullable=False),
    Column("is_active", Boolean, nullable=False, server_default="true"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
Index(
    "ix_attack_scopes_active_expiry",
    attack_scopes.c.is_active,
    attack_scopes.c.authorization_expires_at,
)

attack_simulations = Table(
    "attack_simulations",
    metadata,
    Column("id", String(32), primary_key=True),
    Column("actor_user_id", String(32), ForeignKey("users.id", ondelete="SET NULL")),
    Column(
        "scope_id", String(32), ForeignKey("attack_scopes.id", ondelete="RESTRICT"), nullable=False
    ),
    Column("profile", String(32), nullable=False),
    Column("intensity", String(12), nullable=False),
    Column("duration_minutes", Integer, nullable=False),
    Column("result_json", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
)
Index("ix_attack_simulations_created", attack_simulations.c.created_at)
Index("ix_attack_simulations_scope", attack_simulations.c.scope_id)


def select_database_url(
    runtime_database_url: str | None,
    legacy_database_url: str | None,
    *,
    serverless: bool,
) -> str | None:
    """Prefer the least-privilege runtime credential and fail closed when hosted."""
    if runtime_database_url is not None and runtime_database_url.strip():
        return runtime_database_url
    if serverless:
        return None
    return legacy_database_url


class SecurityDatabase:
    """A small connection-per-operation database facade.

    SQLite remains self-initializing for local development and tests. Hosted
    PostgreSQL is schema-verify-only by default so the runtime role does not
    need CREATE privileges. Provision or change PostgreSQL schema separately
    using an explicitly configured migration connection.
    """

    def __init__(self, database_url: str | None, data_dir: Path) -> None:
        if database_url:
            normalized_url = database_url.strip()
            if normalized_url.startswith("postgres://"):
                normalized_url = normalized_url.replace("postgres://", "postgresql+psycopg://", 1)
            elif normalized_url.startswith("postgresql://"):
                normalized_url = normalized_url.replace("postgresql://", "postgresql+psycopg://", 1)
            if not normalized_url.startswith("postgresql+psycopg://"):
                raise ValueError("NANOU_RUNTIME_DATABASE_URL must use PostgreSQL.")
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
                    "A durable NANOU_RUNTIME_DATABASE_URL is required on serverless hosting."
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

        try:
            if self.mode == "sqlite":
                metadata.create_all(self.engine)
                google_metadata.create_all(self.engine)
            else:
                self._verify_postgres_schema()
            self._ensure_bootstrap_state()
        except Exception:
            self.engine.dispose()
            raise

    def _verify_postgres_schema(self) -> None:
        inspector = inspect(self.engine)
        existing_tables = set(inspector.get_table_names(schema="public"))
        required_tables = {table.name for table in metadata.tables.values()}
        missing_tables = sorted(required_tables - existing_tables)
        missing_columns: list[str] = []
        for table in metadata.tables.values():
            if table.name not in existing_tables:
                continue
            existing_columns = {
                column["name"] for column in inspector.get_columns(table.name, schema="public")
            }
            for column in table.columns:
                if column.name not in existing_columns:
                    missing_columns.append(f"{table.name}.{column.name}")

        if missing_tables or missing_columns:
            details = []
            if missing_tables:
                details.append(f"missing tables: {', '.join(missing_tables)}")
            if missing_columns:
                details.append(f"missing columns: {', '.join(sorted(missing_columns))}")
            raise RuntimeError(
                "PostgreSQL schema is incomplete ("
                + "; ".join(details)
                + "). Run the reviewed schema bootstrap/migration with "
                "NANOU_MIGRATION_DATABASE_URL before starting the application."
            )

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
