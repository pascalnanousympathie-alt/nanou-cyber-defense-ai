import stat
import zipfile

import pytest

from nanou_cyber_ai.malware.ember_archive import safe_extract_ember_archive


def test_safe_extract_accepts_only_flat_jsonl_and_returns_hashes(tmp_path):
    archive = tmp_path / "APK_train.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        zipped.writestr("APK_train_00.jsonl", '{"sha256":"' + "a" * 64 + '","label":1}\n')
    output = tmp_path / "data"

    report = safe_extract_ember_archive(archive, output)

    extracted = output / "APK_train_00.jsonl"
    assert extracted.is_file()
    assert report["files_extracted"] == 1
    assert report["uncompressed_bytes"] == extracted.stat().st_size
    assert report["sha256"]["APK_train_00.jsonl"]


def test_safe_extract_rejects_zip_slip_paths(tmp_path):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        zipped.writestr("../escape.jsonl", '{"label":1}\n')

    with pytest.raises(ValueError, match="Unsafe ZIP member path"):
        safe_extract_ember_archive(archive, tmp_path / "data")
    assert not (tmp_path / "escape.jsonl").exists()


def test_safe_extract_rejects_non_jsonl_and_symlinks(tmp_path):
    non_jsonl = tmp_path / "not-features.zip"
    with zipfile.ZipFile(non_jsonl, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        zipped.writestr("payload.exe", b"MZ")
    with pytest.raises(ValueError, match="Only JSONL"):
        safe_extract_ember_archive(non_jsonl, tmp_path / "data")

    symlink = tmp_path / "symlink.zip"
    info = zipfile.ZipInfo("link.jsonl")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(symlink, "w") as zipped:
        zipped.writestr(info, "target.jsonl")
    with pytest.raises(ValueError, match="symlink"):
        safe_extract_ember_archive(symlink, tmp_path / "symlink-data")


def test_safe_extract_rejects_size_limit_and_overwrite(tmp_path):
    archive = tmp_path / "safe.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        zipped.writestr("APK_test.jsonl", "x" * 200)
    with pytest.raises(ValueError, match="uncompressed-size"):
        safe_extract_ember_archive(
            archive, tmp_path / "limited", max_uncompressed_bytes=100
        )

    output = tmp_path / "existing"
    output.mkdir()
    existing = output / "APK_test.jsonl"
    existing.write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError, match="overwrite"):
        safe_extract_ember_archive(archive, output)
    assert existing.read_text(encoding="utf-8") == "keep"
