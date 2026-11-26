from __future__ import annotations

from pydantic import SecretStr

from nanou_cyber_ai.settings import Settings


def test_runtime_database_url_takes_priority_over_legacy_url() -> None:
    runtime_url = "postgresql://runtime:example@db.example.invalid/app"
    legacy_url = "postgresql://legacy:example@db.example.invalid/app"

    configured = Settings(
        database_url=SecretStr(legacy_url),
        runtime_database_url=SecretStr(runtime_url),
    )

    assert configured.effective_database_url is configured.runtime_database_url
    assert configured.effective_database_url.get_secret_value() == runtime_url


def test_legacy_database_url_remains_a_safe_fallback() -> None:
    legacy_url = "postgresql://legacy:example@db.example.invalid/app"
    configured = Settings(database_url=SecretStr(legacy_url))

    assert configured.effective_database_url is configured.database_url
    assert configured.effective_database_url.get_secret_value() == legacy_url


def test_missing_database_urls_remain_unconfigured() -> None:
    configured = Settings(
        database_url=None,
        runtime_database_url=None,
    )

    assert configured.effective_database_url is None


def test_runtime_database_url_is_loaded_from_environment(monkeypatch) -> None:
    runtime_url = "postgresql://runtime:example@db.example.invalid/app"
    legacy_url = "postgresql://legacy:example@db.example.invalid/app"
    monkeypatch.setenv("NANOU_DATABASE_URL", legacy_url)
    monkeypatch.setenv("NANOU_RUNTIME_DATABASE_URL", runtime_url)

    configured = Settings()

    assert configured.effective_database_url is not None
    assert configured.effective_database_url.get_secret_value() == runtime_url
