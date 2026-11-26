from pathlib import Path

import pytest

from scripts.db_migrate import (
    MigrationError,
    load_migrations,
    validate_target,
)


def test_target_must_be_explicit() -> None:
    with pytest.raises(MigrationError, match="Set NANOU_MIGRATION_TARGET"):
        validate_target(None)


def test_production_is_hard_blocked() -> None:
    with pytest.raises(MigrationError, match="Production migrations are disabled"):
        validate_target("production")


@pytest.mark.parametrize("target", ["development", "preview"])
def test_nonproduction_targets_are_allowed(target: str) -> None:
    assert validate_target(target) == target


def test_load_migrations_orders_files_and_calculates_sha256(tmp_path: Path) -> None:
    (tmp_path / "0002_add_index.sql").write_text(
        "CREATE INDEX ix_probe ON public.probe (id);\n", encoding="utf-8"
    )
    (tmp_path / "0001_create_probe.sql").write_text(
        "CREATE TABLE public.probe (id integer PRIMARY KEY);\n", encoding="utf-8"
    )
    (tmp_path / "notes.txt").write_text("not a migration", encoding="utf-8")

    migrations = load_migrations(tmp_path)

    assert [migration.version for migration in migrations] == ["0001", "0002"]
    assert len(migrations[0].checksum) == 64
    assert migrations[0].sql.startswith("CREATE TABLE")


def test_invalid_migration_filename_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "create_table.sql").write_text("SELECT 1;", encoding="utf-8")

    with pytest.raises(MigrationError, match="Invalid migration filename"):
        load_migrations(tmp_path)


def test_empty_migration_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "0001_empty.sql").write_text("  \n", encoding="utf-8")

    with pytest.raises(MigrationError, match="Migration is empty"):
        load_migrations(tmp_path)


def test_missing_migration_directory_is_empty(tmp_path: Path) -> None:
    assert load_migrations(tmp_path / "missing") == []
