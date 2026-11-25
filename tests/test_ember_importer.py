import sys
from types import SimpleNamespace

from scripts import import_ember2024_archives as importer


def test_importer_pins_dataset_revision_and_safe_extracts(tmp_path, monkeypatch):
    calls = {}

    def fake_download(**kwargs):
        calls.update(kwargs)
        archive = tmp_path / kwargs["filename"]
        archive.write_bytes(b"test-archive")
        return archive

    extracted = {}

    def fake_extract(archive_path, output_dir, *, max_uncompressed_bytes):
        extracted.update(
            {
                "archive_path": archive_path,
                "output_dir": output_dir,
                "max_uncompressed_bytes": max_uncompressed_bytes,
            }
        )
        return {"files_extracted": 1}

    monkeypatch.setitem(
        sys.modules,
        "huggingface_hub",
        SimpleNamespace(hf_hub_download=fake_download),
    )
    monkeypatch.setattr(importer, "safe_extract_ember_archive", fake_extract)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "import_ember2024_archives.py",
            "--data-dir",
            str(tmp_path / "dataset"),
            "--subset",
            "train",
            "--file-type",
            "APK",
        ],
    )

    assert importer.main() == 0
    assert calls == {
        "repo_id": "joyce8/EMBER2024",
        "filename": "APK_train.zip",
        "repo_type": "dataset",
        "revision": "3d23efef7c0f0b702c5024400cfff4c3744a3832",
    }
    assert extracted["archive_path"] == tmp_path / "APK_train.zip"
    assert extracted["output_dir"] == tmp_path / "dataset"
    assert extracted["max_uncompressed_bytes"] == importer.DEFAULT_MAX_UNCOMPRESSED_BYTES
