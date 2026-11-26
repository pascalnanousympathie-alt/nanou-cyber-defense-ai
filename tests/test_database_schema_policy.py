from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from nanou_cyber_ai.storage.bootstrap import bootstrap_schema, main, normalize_postgres_url
from nanou_cyber_ai.storage.database import SecurityDatabase, metadata


POSTGRES_URL = "postgresql+psycopg://runtime:placeholder@db.example.invalid/nanou_test"


def test_sqlite_still_creates_schema_for_local_development(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("AWS_LAMBDA_FUNCTION_NAME", raising=False)

    from sqlalchemy import inspect

    database = SecurityDatabase(None, tmp_path)
    try:
        tables = set(inspect(database.engine).get_table_names())
        assert set(metadata.tables).issubset(tables)
    finally:
        database.close()


def test_postgres_runtime_verifies_schema_without_running_ddl(tmp_path) -> None:
    required_tables = sorted(metadata.tables)
    fake_engine = MagicMock()
    fake_inspector = MagicMock()
    fake_inspector.get_table_names.return_value = required_tables
    fake_inspector.get_columns.side_effect = lambda table, schema: [
        {"name": column.name} for column in metadata.tables[table].columns
    ]

    with (
        patch("nanou_cyber_ai.storage.database.create_engine", return_value=fake_engine),
        patch("nanou_cyber_ai.storage.database.inspect", return_value=fake_inspector),
        patch("nanou_cyber_ai.storage.database.metadata.create_all") as create_all,
        patch.object(SecurityDatabase, "_ensure_bootstrap_state"),
    ):
        database = SecurityDatabase(POSTGRES_URL, tmp_path)
        database.close()

    create_all.assert_not_called()
    fake_inspector.get_table_names.assert_called_once_with(schema="public")
    fake_engine.dispose.assert_called_once()


def test_postgres_runtime_fails_closed_when_schema_is_incomplete(tmp_path) -> None:
    required_tables = sorted(metadata.tables)
    fake_engine = MagicMock()
    fake_inspector = MagicMock()
    fake_inspector.get_table_names.return_value = required_tables[:-1]

    with (
        patch("nanou_cyber_ai.storage.database.create_engine", return_value=fake_engine),
        patch("nanou_cyber_ai.storage.database.inspect", return_value=fake_inspector),
        patch("nanou_cyber_ai.storage.database.metadata.create_all") as create_all,
        patch.object(SecurityDatabase, "_ensure_bootstrap_state") as ensure_bootstrap,
        pytest.raises(RuntimeError, match="schema is incomplete"),
    ):
        SecurityDatabase(POSTGRES_URL, tmp_path)

    create_all.assert_not_called()
    ensure_bootstrap.assert_not_called()
    fake_engine.dispose.assert_called_once()


def test_postgres_runtime_fails_closed_when_required_column_is_missing(tmp_path) -> None:
    required_tables = sorted(metadata.tables)
    fake_engine = MagicMock()
    fake_inspector = MagicMock()
    fake_inspector.get_table_names.return_value = required_tables

    def columns_for(table: str, schema: str) -> list[dict[str, str]]:
        columns = [{"name": column.name} for column in metadata.tables[table].columns]
        if table == "users":
            return columns[:-1]
        return columns

    fake_inspector.get_columns.side_effect = columns_for

    with (
        patch("nanou_cyber_ai.storage.database.create_engine", return_value=fake_engine),
        patch("nanou_cyber_ai.storage.database.inspect", return_value=fake_inspector),
        patch("nanou_cyber_ai.storage.database.metadata.create_all") as create_all,
        patch.object(SecurityDatabase, "_ensure_bootstrap_state") as ensure_bootstrap,
        pytest.raises(RuntimeError, match="users.updated_at"),
    ):
        SecurityDatabase(POSTGRES_URL, tmp_path)

    create_all.assert_not_called()
    ensure_bootstrap.assert_not_called()
    fake_engine.dispose.assert_called_once()


def test_migration_url_must_be_postgresql() -> None:
    assert normalize_postgres_url("postgres://u:p@db.example.invalid/app") == (
        "postgresql+psycopg://u:p@db.example.invalid/app"
    )
    assert normalize_postgres_url("postgresql://u:p@db.example.invalid/app") == (
        "postgresql+psycopg://u:p@db.example.invalid/app"
    )
    with pytest.raises(ValueError, match="must use PostgreSQL"):
        normalize_postgres_url("sqlite:///local.db")


def test_schema_bootstrap_uses_migration_url_and_is_idempotent() -> None:
    from sqlalchemy.dialects import postgresql

    fake_engine = MagicMock()
    fake_connection = fake_engine.begin.return_value.__enter__.return_value

    with (
        patch(
            "nanou_cyber_ai.storage.bootstrap.create_engine",
            return_value=fake_engine,
        ) as create_engine,
        patch("nanou_cyber_ai.storage.bootstrap.metadata.create_all") as create_all,
    ):
        bootstrap_schema("postgresql://migrator:placeholder@db.example.invalid/nanou_test")

    args, kwargs = create_engine.call_args
    assert args == ("postgresql+psycopg://migrator:placeholder@db.example.invalid/nanou_test",)
    assert kwargs["connect_args"] == {"sslmode": "require", "prepare_threshold": None}
    create_all.assert_called_once_with(fake_engine)
    fake_connection.execute.assert_called_once()
    statement = fake_connection.execute.call_args.args[0]
    assert "ON CONFLICT" in str(statement.compile(dialect=postgresql.dialect()))
    fake_engine.dispose.assert_called_once()


def test_bootstrap_command_requires_migration_url(monkeypatch, capsys) -> None:
    monkeypatch.delenv("NANOU_MIGRATION_DATABASE_URL", raising=False)

    assert main() == 2
    captured = capsys.readouterr()
    assert "NANOU_MIGRATION_DATABASE_URL is required" in captured.err
    assert "placeholder" not in captured.err
