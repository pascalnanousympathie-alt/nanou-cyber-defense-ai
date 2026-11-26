"""Convert a PostgreSQL URI into a safely quoted libpq environment file."""

from __future__ import annotations

import argparse
import os
import shlex
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

_SUPPORTED_OPTIONS = {
    "sslmode": "PGSSLMODE",
    "channel_binding": "PGCHANNELBINDING",
    "application_name": "PGAPPNAME",
    "connect_timeout": "PGCONNECT_TIMEOUT",
    "target_session_attrs": "PGTARGETSESSIONATTRS",
}
_ALLOWED_SSL_MODES = {"require", "verify-ca", "verify-full"}


def parse_postgres_uri(uri: str) -> dict[str, str]:
    """Validate a PostgreSQL URI and return libpq environment settings."""
    try:
        parsed = urlsplit(uri)
        host = parsed.hostname
        port = parsed.port or 5432
    except ValueError as exc:
        raise ValueError("Invalid PostgreSQL connection URI.") from exc

    if parsed.scheme not in {"postgres", "postgresql"} or not host:
        raise ValueError("NANOU_BACKUP_DATABASE_URL must be a PostgreSQL URI.")
    if (
        parsed.username is None
        or parsed.password is None
        or not unquote(parsed.username)
        or not unquote(parsed.password)
        or not parsed.path.strip("/")
    ):
        raise ValueError("Backup database URI must include a username, password and database.")
    if parsed.fragment:
        raise ValueError("PostgreSQL connection URI must not contain a fragment.")

    query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=False)
    unsupported = sorted(set(query) - set(_SUPPORTED_OPTIONS))
    if unsupported:
        raise ValueError("Unsupported PostgreSQL URI query options: " + ", ".join(unsupported))
    if any(len(values) != 1 for values in query.values()):
        raise ValueError("PostgreSQL URI query options must not be repeated.")

    sslmode = query.get("sslmode", ["require"])[0]
    if sslmode not in _ALLOWED_SSL_MODES:
        raise ValueError("PostgreSQL backup connections must require TLS.")

    database = unquote(parsed.path.lstrip("/"))
    username = unquote(parsed.username)
    password = unquote(parsed.password)
    if not database.strip() or not username.strip() or not password:
        raise ValueError("Backup database URI must include a username, password and database.")

    values = {
        "PGHOST": host,
        "PGPORT": str(port),
        "PGDATABASE": database,
        "PGUSER": username,
        "PGPASSWORD": password,
        "PGSSLMODE": sslmode,
    }
    for option, environment_name in _SUPPORTED_OPTIONS.items():
        if option in query:
            values[environment_name] = query[option][0]

    if any(chr(0) in value for value in values.values()):
        raise ValueError("PostgreSQL connection settings contain an invalid NUL byte.")
    return values


def write_libpq_environment(uri: str, output_path: Path) -> None:
    """Write validated libpq settings with shell-safe quoting and mode 0600."""
    values = parse_postgres_uri(uri)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(output_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            for key, value in values.items():
                output.write(f"export {key}={shlex.quote(value)}\n")
    except Exception:
        output_path.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write a safely quoted libpq environment file from DATABASE_URL."
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    uri = os.environ.get("DATABASE_URL")
    if not uri:
        parser.error("DATABASE_URL is required in the environment.")
    try:
        write_libpq_environment(uri, args.output)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print("Validated PostgreSQL connection settings written securely.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
