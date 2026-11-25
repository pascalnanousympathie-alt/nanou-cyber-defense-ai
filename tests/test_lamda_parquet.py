import csv
from pathlib import Path

import pytest

from nanou_cyber_ai.malware.lamda import prepare_lamda_parquet

pyarrow = pytest.importorskip("pyarrow")
parquet = pytest.importorskip("pyarrow.parquet")


FEATURE_NAMES = [f"feat_{index}" for index in range(4561)]


def _write_parquet(
    path: Path,
    hashes: list[str],
    labels: list[int],
    *,
    binary_hashes: bool = False,
    invalid_feature_type: str | None = None,
) -> None:
    values = {
        "hash": [bytes.fromhex(value) for value in hashes] if binary_hashes else hashes,
        "label": labels,
        "family": ["family-a" if label else "benign" for label in labels],
        "vt_count": [4 if label else 0 for label in labels],
        "year_month": ["2022-01"] * len(labels),
    }
    for feature_index, name in enumerate(FEATURE_NAMES):
        feature_values = [(row_index + feature_index) % 3 for row_index in range(len(labels))]
        feature_type = pyarrow.int16() if invalid_feature_type == name else pyarrow.int8()
        values[name] = pyarrow.array(feature_values, type=feature_type)
    parquet.write_table(pyarrow.table(values), path)


def _hash(number: int) -> str:
    return f"{number:064x}"


def test_lamda_prepare_drops_cross_split_hash_overlap_and_exports_int8_features(
    tmp_path: Path,
) -> None:
    train_source = tmp_path / "2022_train.parquet"
    test_source = tmp_path / "2023_test.parquet"
    train_csv = tmp_path / "train.csv"
    test_csv = tmp_path / "test.csv"
    _write_parquet(train_source, [_hash(i) for i in (1, 2, 3, 4)], [0, 0, 1, 1], binary_hashes=True)
    _write_parquet(test_source, [_hash(i) for i in (3, 5, 6, 7)], [0, 0, 1, 0], binary_hashes=True)

    result = prepare_lamda_parquet(
        train_source,
        test_source,
        train_csv,
        test_csv,
        max_train_rows=3,
        max_test_rows=20,
        sampling_seed=17,
    )

    assert result["feature_count"] == 4561
    assert result["cross_split_hash_overlap_dropped_from_train"] == 1
    assert result["cross_split_label_conflicts_dropped_from_train"] == 1
    assert result["train_sample"]["rows"] == 3
    assert result["train_sample"]["label_counts"] == {"0": 2, "1": 1}
    assert result["test_sample"]["rows"] == 4
    assert result["train_sample"]["sha256_overlap_with_test"] == 0

    with train_csv.open(newline="", encoding="utf-8") as handle:
        train_rows = list(csv.DictReader(handle))
    with test_csv.open(newline="", encoding="utf-8") as handle:
        test_rows = list(csv.DictReader(handle))
    train_hashes = {row["sha256"] for row in train_rows}
    test_hashes = {row["sha256"] for row in test_rows}
    assert train_hashes.isdisjoint(test_hashes)
    assert len(train_rows) == 3
    assert len(test_rows) == 4
    assert len(train_rows[0]) == 4563
    assert set(train_rows[0][name] for name in ("feat_0", "feat_1")) <= {"0", "1", "2"}


def test_lamda_prepare_is_deterministic_and_refuses_overwrite(tmp_path: Path) -> None:
    train_source = tmp_path / "2022_train.parquet"
    test_source = tmp_path / "2023_test.parquet"
    _write_parquet(train_source, [_hash(i) for i in range(10, 18)], [0, 1] * 4)
    _write_parquet(test_source, [_hash(i) for i in range(20, 24)], [0, 1] * 2)

    first_train = tmp_path / "first-train.csv"
    first_test = tmp_path / "first-test.csv"
    second_train = tmp_path / "second-train.csv"
    second_test = tmp_path / "second-test.csv"
    prepare_lamda_parquet(
        train_source,
        test_source,
        first_train,
        first_test,
        max_train_rows=4,
        sampling_seed=2026,
    )
    prepare_lamda_parquet(
        train_source,
        test_source,
        second_train,
        second_test,
        max_train_rows=4,
        sampling_seed=2026,
    )
    assert first_train.read_bytes() == second_train.read_bytes()
    assert first_test.read_bytes() == second_test.read_bytes()

    with pytest.raises(FileExistsError):
        prepare_lamda_parquet(train_source, test_source, first_train, tmp_path / "unused.csv")


def test_lamda_prepare_preserves_signed_int8_feature_values(tmp_path: Path) -> None:
    train_source = tmp_path / "2022_train.parquet"
    test_source = tmp_path / "2023_test.parquet"
    train_csv = tmp_path / "train.csv"
    test_csv = tmp_path / "test.csv"
    _write_parquet(train_source, [_hash(i) for i in (30, 31)], [0, 1])
    _write_parquet(test_source, [_hash(i) for i in (40, 41)], [0, 1])
    table = parquet.read_table(test_source)
    table = table.set_column(
        table.schema.get_field_index("feat_19"),
        "feat_19",
        pyarrow.array([-1, 2], type=pyarrow.int8()),
    )
    parquet.write_table(table, test_source)

    prepare_lamda_parquet(train_source, test_source, train_csv, test_csv)
    with test_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert sorted(int(row["feat_19"]) for row in rows) == [-1, 2]


def test_lamda_prepare_rejects_non_int8_feature_columns(tmp_path: Path) -> None:
    train_source = tmp_path / "2022_train.parquet"
    test_source = tmp_path / "2023_test.parquet"
    _write_parquet(train_source, [_hash(i) for i in (30, 31)], [0, 1])
    _write_parquet(
        test_source,
        [_hash(i) for i in (40, 41)],
        [0, 1],
        invalid_feature_type="feat_19",
    )

    with pytest.raises(ValueError, match="non-null int8"):
        prepare_lamda_parquet(
            train_source,
            test_source,
            tmp_path / "train.csv",
            tmp_path / "test.csv",
        )


def test_lamda_prepare_rejects_duplicate_hashes_within_split(tmp_path: Path) -> None:
    train_source = tmp_path / "2022_train.parquet"
    test_source = tmp_path / "2023_test.parquet"
    _write_parquet(train_source, [_hash(50), _hash(50)], [0, 1])
    _write_parquet(test_source, [_hash(60), _hash(61)], [0, 1])

    with pytest.raises(ValueError, match="Duplicate SHA-256"):
        prepare_lamda_parquet(
            train_source,
            test_source,
            tmp_path / "train.csv",
            tmp_path / "test.csv",
        )
