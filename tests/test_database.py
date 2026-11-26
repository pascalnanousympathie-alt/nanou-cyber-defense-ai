import pytest

from nanou_cyber_ai.storage.database import SecurityDatabase, select_database_url


def test_runtime_database_url_takes_precedence_over_legacy() -> None:
    selected = select_database_url(
        "postgresql://runtime.example/db",
        "postgresql://legacy.example/db",
        serverless=True,
    )
    assert selected == "postgresql://runtime.example/db"


def test_serverless_fails_closed_without_runtime_url_even_if_legacy_exists() -> None:
    selected = select_database_url(
        None, "postgresql://legacy.example/db", serverless=True
    )
    assert selected is None


def test_local_development_can_fall_back_to_legacy_database_url() -> None:
    selected = select_database_url(
        None, "postgresql://legacy.example/db", serverless=False
    )
    assert selected == "postgresql://legacy.example/db"


def test_serverless_database_rejects_sqlite_fallback(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("VERCEL", "1")
    with pytest.raises(RuntimeError, match="NANOU_RUNTIME_DATABASE_URL"):
        SecurityDatabase(None, tmp_path)


def test_postgresql_runtime_does_not_attempt_schema_ddl(monkeypatch, tmp_path) -> None:
    import nanou_cyber_ai.storage.database as database_module

    engine = object()
    monkeypatch.setattr(database_module, "create_engine", lambda *args, **kwargs: engine)
    monkeypatch.setattr(
        database_module.metadata,
        "create_all",
        lambda _engine: pytest.fail("PostgreSQL runtime must not issue schema DDL"),
    )
    monkeypatch.setattr(SecurityDatabase, "_ensure_bootstrap_state", lambda _self: None)

    database = SecurityDatabase("postgresql://runtime.example/db", tmp_path)

    assert database.mode == "postgresql"
    assert database.engine is engine


def test_settings_loads_runtime_database_url_from_environment(monkeypatch) -> None:
    from nanou_cyber_ai.settings import Settings

    monkeypatch.setenv("NANOU_RUNTIME_DATABASE_URL", "postgresql://runtime.example/db")
    monkeypatch.setenv("NANOU_DATABASE_URL", "postgresql://legacy.example/db")
    configured = Settings(_env_file=None)

    assert configured.runtime_database_url is not None
    assert configured.runtime_database_url.get_secret_value() == "postgresql://runtime.example/db"
    assert configured.database_url is not None
    assert configured.database_url.get_secret_value() == "postgresql://legacy.example/db"
