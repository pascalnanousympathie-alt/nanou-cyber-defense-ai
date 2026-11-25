import csv
import json

import pytest

from nanou_cyber_ai.malware.ember import export_ember_jsonl_subset

np = pytest.importorskip("numpy")


class FakeExtractor:
    dim = 2

    def process_raw_features(self, record):
        return np.asarray(record["features"], dtype=np.float32)


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_raw_jsonl_export_uses_extractor_and_deduplicates_hashes(tmp_path):
    source = tmp_path / "source"
    _write_jsonl(
        source / "APK_train.jsonl",
        [
            {"sha256": "a" * 64, "label": 1, "features": [1.5, 2.5]},
            {"sha256": "b" * 64, "label": None, "features": [3.5, 4.5]},
            {"sha256": "c" * 64, "label": 0, "features": [5.5, 6.5]},
            {"sha256": "a" * 64, "label": 1, "features": [1.5, 2.5]},
        ],
    )
    output = tmp_path / "export" / "train.csv"

    report = export_ember_jsonl_subset(
        source,
        output,
        subset="train",
        max_source_rows=10,
        extractor=FakeExtractor(),
    )

    with output.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert report["source_rows_scanned"] == 4
    assert report["labeled_rows_exported"] == 2
    assert report["unlabeled_rows_skipped"] == 1
    assert report["duplicate_source_rows_skipped"] == 1
    assert rows[0]["sha256"] == "a" * 64
    assert rows[0]["label"] == "1"
    assert rows[0]["ember_feature_0000"] == "1.5"
    assert rows[1]["sha256"] == "c" * 64


def test_raw_jsonl_export_enforces_unique_export_cap(tmp_path):
    source = tmp_path / "source"
    _write_jsonl(
        source / "APK_test.jsonl",
        [
            {"sha256": "a" * 64, "label": 1, "features": [1, 2]},
            {"sha256": "a" * 64, "label": 1, "features": [1, 2]},
            {"sha256": "b" * 64, "label": 0, "features": [2, 3]},
            {"sha256": "c" * 64, "label": 1, "features": [3, 4]},
        ],
    )

    report = export_ember_jsonl_subset(
        source,
        tmp_path / "test.csv",
        subset="test",
        max_source_rows=4,
        max_exported_rows=2,
        extractor=FakeExtractor(),
    )
    assert report["source_rows_scanned"] == 3
    assert report["labeled_rows_exported"] == 2
    assert report["duplicate_source_rows_skipped"] == 1


def test_raw_jsonl_export_rejects_conflicting_duplicate_hashes(tmp_path):
    source = tmp_path / "source"
    _write_jsonl(
        source / "APK_train.jsonl",
        [
            {"sha256": "a" * 64, "label": 1, "features": [1, 2]},
            {"sha256": "a" * 64, "label": 1, "features": [1, 3]},
        ],
    )

    with pytest.raises(ValueError, match="Duplicate SHA-256 has conflicting"):
        export_ember_jsonl_subset(
            source,
            tmp_path / "conflict.csv",
            subset="train",
            max_source_rows=2,
            extractor=FakeExtractor(),
        )


def test_official_thrember_feature_extractor_is_importable():
    try:
        import thrember
    except ModuleNotFoundError as exc:
        if exc.name == "thrember":
            pytest.skip("Install the optional pinned EMBER extractor to run this check.")
        raise

    from signify.authenticode import SignedPEFile
    from thrember import PEFeatureExtractor

    assert callable(SignedPEFile)
    assert hasattr(SignedPEFile, "iter_signed_datas")
    extractor = PEFeatureExtractor()
    assert extractor.dim >= 2000
