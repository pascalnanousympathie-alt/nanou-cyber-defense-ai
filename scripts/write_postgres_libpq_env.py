"""Command-line wrapper for safely exporting libpq environment variables."""

from __future__ import annotations


def main() -> int:
    from nanou_cyber_ai.backup.connection import main as run_connection_parser

    return run_connection_parser()


if __name__ == "__main__":
    raise SystemExit(main())
