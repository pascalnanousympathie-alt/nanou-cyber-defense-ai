from pathlib import Path

import pytest

from scripts.db_migrate import (
    PREVIEW_ALLOWED_DATABASE,
    PREVIEW_ALLOWED_HOST,
    MigrationError,
    load_migrations,
    validate_database_target,
    validate_role_flags,
    validate_session_roles,
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


def test_database_session_requires_dedicated_login_and_owner_role() -> None:
    validate_session_roles("nanou_migration_owner", "nanou_migration_login")


@pytest.mark.parametrize(
    ("effective_role", "login_role"),
    [
        ("nanou_app", "nanou_app"),
        ("nanou_migration_owner", "nanou_app"),
        ("nanou_runtime", "nanou_runtime"),
    ],
)
def test_database_session_rejects_non_migration_identity(
    effective_role: str, login_role: str
) -> None:
    with pytest.raises(MigrationError, match="dedicated migration login"):
        validate_session_roles(effective_role, login_role)


def test_symlink_migration_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "outside.sql"
    target.write_text("SELECT 1;", encoding="utf-8")
    (tmp_path / "0001_link.sql").symlink_to(target)

    with pytest.raises(MigrationError, match="must not be a symlink"):
        load_migrations(tmp_path)


def test_database_target_allows_only_the_pinned_preview_database() -> None:
    url = (
        f"postgresql://migration@{PREVIEW_ALLOWED_HOST}:5432/"
        f"{PREVIEW_ALLOWED_DATABASE}"
    )
    validate_database_target(url, "preview")


def test_database_target_rejects_production_host_even_if_mislabeled_preview() -> None:
    url = "postgresql://migration@production.neon.tech:5432/nanou_preview"
    with pytest.raises(MigrationError, match="approved isolated Preview database"):
        validate_database_target(url, "preview")


def test_database_target_rejects_preview_host_with_production_target() -> None:
    url = (
        f"postgresql://migration@{PREVIEW_ALLOWED_HOST}:5432/"
        f"{PREVIEW_ALLOWED_DATABASE}"
    )
    with pytest.raises(MigrationError, match="Production migrations are disabled"):
        validate_database_target(url, "production")


def test_database_target_rejects_other_database_on_preview_host() -> None:
    url = f"postgresql://migration@{PREVIEW_ALLOWED_HOST}:5432/postgres"
    with pytest.raises(MigrationError, match="approved isolated Preview database"):
        validate_database_target(url, "preview")


def test_migration_role_flags_require_login_and_no_login_owner() -> None:
    validate_role_flags(
        (True, False, False, False, False, False, False, False, False, False, False, False)
    )


def test_migration_role_flags_reject_elevated_login_or_owner() -> None:
    with pytest.raises(MigrationError, match="unsafe PostgreSQL attributes"):
        validate_role_flags(
            (True, True, False, False, False, False, False, False, False, False, False, False)
        )


def test_migration_role_flags_reject_missing_roles() -> None:
    with pytest.raises(MigrationError, match="Could not verify migration role attributes"):
        validate_role_flags(())
