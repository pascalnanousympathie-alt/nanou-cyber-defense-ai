from __future__ import annotations

import shlex
from pathlib import Path

import pytest

from nanou_cyber_ai.backup.connection import parse_postgres_uri, write_libpq_environment


def test_parse_postgres_uri_decodes_credentials_and_defaults_to_tls() -> None:
    values = parse_postgres_uri(
        "postgresql://backup%40role:p%40ss%3Aword%2F%23%24@db.example:5433/"
        "nanou%5Fcyber?channel_binding=require&application_name=nanou-backup"
    )

    assert values == {
        "PGHOST": "db.example",
        "PGPORT": "5433",
        "PGDATABASE": "nanou_cyber",
        "PGUSER": "backup@role",
        "PGPASSWORD": "p@ss:word/#$",
        "PGSSLMODE": "require",
        "PGCHANNELBINDING": "require",
        "PGAPPNAME": "nanou-backup",
    }


def test_parse_postgres_uri_accepts_only_secure_ssl_modes() -> None:
    for sslmode in ("require", "verify-ca", "verify-full"):
        assert (
            parse_postgres_uri(f"postgres://backup:secret@db.example/nanou?sslmode={sslmode}")[
                "PGSSLMODE"
            ]
            == sslmode
        )

    with pytest.raises(ValueError, match="require TLS"):
        parse_postgres_uri("postgres://backup:secret@db.example/nanou?sslmode=disable")


def test_parse_postgres_uri_rejects_missing_credentials_and_database() -> None:
    invalid = (
        "https://backup:secret@db.example/nanou",
        "postgres://backup@db.example/nanou",
        "postgres://:secret@db.example/nanou",
        "postgres://backup:secret@db.example/",
        "postgres://backup:secret@db.example/%20",
    )
    for uri in invalid:
        with pytest.raises(ValueError):
            parse_postgres_uri(uri)


def test_parse_postgres_uri_rejects_unknown_or_duplicate_query_options() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        parse_postgres_uri("postgres://backup:secret@db.example/nanou?sslrootcert=/tmp/ca.pem")
    with pytest.raises(ValueError, match="must not be repeated"):
        parse_postgres_uri(
            "postgres://backup:secret@db.example/nanou?sslmode=require&sslmode=verify-full"
        )


def test_parse_postgres_uri_rejects_fragments_and_invalid_ports() -> None:
    with pytest.raises(ValueError, match="fragment"):
        parse_postgres_uri("postgres://backup:secret@db.example/nanou#fragment")
    with pytest.raises(ValueError, match="Invalid PostgreSQL"):
        parse_postgres_uri("postgres://backup:secret@db.example:99999/nanou")


def test_write_libpq_environment_quotes_values_and_restricts_permissions(
    tmp_path: Path,
) -> None:
    output = tmp_path / "secure" / "connection.env"
    uri = "postgres://backup:p%40ss%24word@db.example/nanou?sslmode=require"

    write_libpq_environment(uri, output)

    assert output.stat().st_mode & 0o777 == 0o600
    environment = {}
    for line in output.read_text(encoding="utf-8").splitlines():
        assignment = line.removeprefix("export ")
        key, value = assignment.split("=", 1)
        environment[key] = shlex.split(value)[0]
    assert environment["PGPASSWORD"] == "p@ss$word"
    assert environment["PGSSLMODE"] == "require"
