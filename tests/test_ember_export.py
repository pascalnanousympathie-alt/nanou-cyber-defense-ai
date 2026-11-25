import csv
import json
import struct

import pytest

from nanou_cyber_ai.malware.ember import export_ember_vectorized_subset


def _make_dataset(directory, labels, metadata, vectors, subset="train"):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / f"X_{subset}.dat").open("wb") as stream:
        for vector in vectors:
            stream.write(struct.pack("<" + "f" * len(vector), *vector))
    with (directory / f"y_{subset}.dat").open("wb") as stream:
        for label in labels:
            stream.write(struct.pack("<f", label))
    with (directory / f"APK_{subset}.jsonl").open("w", encoding="utf-8") as stream:
        for record in metadata:
            stream.write(json.dumps(record) + "\n")


def test_export_joins_hashes_labels_and_features_and_skips_unlabeled(tmp_path):
    source = tmp_path / "source"
    metadata = [
        {"sha256": "a" * 64, "label": 1},
        {"sha256": "b" * 64, "label": None},
        {"sha256": "c" * 64, "label": 0},
        {"sha256": "a" * 64, "label": 1},
    ]
    _make_dataset(
        source,
        [1, -1, 0, 1],
        metadata,
        [[1.5, 2.5], [3.5, 4.5], [5.5, 6.5], [1.5, 2.5]],
    )
    output = tmp_path / "export" / "train.csv"

    report = export_ember_vectorized_subset(source, output, subset="train", max_source_rows=10)

    with output.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert report["source_rows_scanned"] == 4
    assert report["labeled_rows_exported"] == 2
    assert report["unlabeled_rows_skipped"] == 1
    assert report["duplicate_source_rows_skipped"] == 1
    assert rows[0]["sha256"] == "a" * 64
    assert rows[0]["label"] == "1"
    assert rows[0]["ember_feature_0000"] == "1.5"
    assert rows[1]["sha256"] == "c" * 64
    assert rows[1]["label"] == "0"


def test_export_checks_metadata_vector_label_alignment_and_preserves_output(tmp_path):
    source = tmp_path / "source"
    _make_dataset(
        source,
        [1],
        [{"sha256": "a" * 64, "label": 0}],
        [[1.0, 2.0]],
    )
    output = tmp_path / "existing.csv"
    output.write_text("keep-existing-file\n", encoding="utf-8")

    with pytest.raises(ValueError, match="label mismatch"):
        export_ember_vectorized_subset(source, output, subset="train", max_source_rows=1)

    assert output.read_text(encoding="utf-8") == "keep-existing-file\n"


def test_export_rejects_conflicting_duplicate_hashes(tmp_path):
    source = tmp_path / "source"
    _make_dataset(
        source,
        [1, 1],
        [
            {"sha256": "a" * 64, "label": 1},
            {"sha256": "a" * 64, "label": 1},
        ],
        [[1.0, 2.0], [1.0, 3.0]],
    )

    with pytest.raises(ValueError, match="Duplicate SHA-256 has conflicting"):
        export_ember_vectorized_subset(
            source, tmp_path / "out.csv", subset="train", max_source_rows=2
        )


def test_export_stops_at_max_unique_exported_rows(tmp_path):
    source = tmp_path / "source"
    _make_dataset(
        source,
        [1, 1, 0, 1],
        [
            {"sha256": "a" * 64, "label": 1},
            {"sha256": "a" * 64, "label": 1},
            {"sha256": "b" * 64, "label": 0},
            {"sha256": "c" * 64, "label": 1},
        ],
        [[1.0], [1.0], [2.0], [3.0]],
    )

    report = export_ember_vectorized_subset(
        source,
        tmp_path / "limited-unique.csv",
        subset="train",
        max_source_rows=4,
        max_exported_rows=2,
    )

    assert report["source_rows_scanned"] == 3
    assert report["labeled_rows_exported"] == 2
    assert report["duplicate_source_rows_skipped"] == 1


def test_export_obeys_source_row_limit(tmp_path):
    source = tmp_path / "source"
    _make_dataset(
        source,
        [1, 0, 1],
        [
            {"sha256": "a" * 64, "label": 1},
            {"sha256": "b" * 64, "label": 0},
            {"sha256": "c" * 64, "label": 1},
        ],
        [[1.0], [2.0], [3.0]],
    )
    output = tmp_path / "limited.csv"
    report = export_ember_vectorized_subset(source, output, subset="train", max_source_rows=2)
    assert report["source_rows_scanned"] == 2
    assert report["labeled_rows_exported"] == 2
    with output.open(newline="", encoding="utf-8") as stream:
        assert len(list(csv.DictReader(stream))) == 2


def test_export_rejects_missing_metadata_and_feature_dimension_limit(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "X_train.dat").write_bytes(struct.pack("<ff", 1.0, 2.0))
    (source / "y_train.dat").write_bytes(struct.pack("<f", 1))
    with pytest.raises(ValueError, match="JSONL"):
        export_ember_vectorized_subset(
            source, tmp_path / "out.csv", subset="train", max_source_rows=1
        )
    (source / "APK_train.jsonl").write_text(
        json.dumps({"sha256": "a" * 64, "label": 1}) + "\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="dimension"):
        export_ember_vectorized_subset(
            source, tmp_path / "out.csv", subset="train", max_source_rows=1, max_features=1
        )


@pytest.mark.parametrize("invalid_label", [0.5, float("nan"), float("inf")])
def test_export_rejects_non_binary_float32_labels(tmp_path, invalid_label):
    source = tmp_path / "source"
    source.mkdir()
    (source / "X_train.dat").write_bytes(struct.pack("<ff", 1.0, 2.0))
    (source / "y_train.dat").write_bytes(struct.pack("<f", invalid_label))
    (source / "APK_train.jsonl").write_text(
        json.dumps({"sha256": "a" * 64, "label": 1}) + "\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="finite integer"):
        export_ember_vectorized_subset(
            source, tmp_path / "invalid.csv", subset="train", max_source_rows=1
        )
