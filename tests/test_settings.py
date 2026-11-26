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


def test_legacy_database_url_remains_a_local_development_fallback(monkeypatch) -> None:
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("AWS_LAMBDA_FUNCTION_NAME", raising=False)
    legacy_url = "postgresql://legacy:example@db.example.invalid/app"
    configured = Settings(database_url=SecretStr(legacy_url))

    assert configured.effective_database_url is configured.database_url
    assert configured.effective_database_url.get_secret_value() == legacy_url


def test_blank_runtime_url_uses_legacy_only_for_local_development(monkeypatch) -> None:
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("AWS_LAMBDA_FUNCTION_NAME", raising=False)
    legacy_url = "postgresql://legacy:example@db.example.invalid/app"
    configured = Settings(
        database_url=SecretStr(legacy_url),
        runtime_database_url=SecretStr(""),
    )

    assert configured.effective_database_url is configured.database_url


def test_serverless_never_falls_back_to_legacy_owner_url(monkeypatch) -> None:
    monkeypatch.setenv("VERCEL", "1")
    legacy_url = "postgresql://legacy:example@db.example.invalid/app"
    configured = Settings(
        database_url=SecretStr(legacy_url),
        runtime_database_url=SecretStr(""),
    )

    assert configured.effective_database_url is None


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
