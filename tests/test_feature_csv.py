import csv
import io

import pytest

from nanou_cyber_ai.malware.feature_csv import prepare_feature_csv
from nanou_cyber_ai.malware.inference import expected_feature_names


def _csv_for(dataset_id: str, values: list[int | float], *, extra_rows: int = 0) -> str:
    headers = ["sha256", "label", *expected_feature_names(dataset_id)]
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerow(["a" * 64, "benign", *values])
    for _ in range(extra_rows):
        writer.writerow(["b" * 64, "malicious", *values])
    return output.getvalue()


def test_prepare_ember_csv_preserves_exact_feature_order_and_hash() -> None:
    values = [float(index) for index in range(2568)]
    result = prepare_feature_csv(_csv_for("ember2024-apk", values), "ember2024-apk")

    assert result["feature_count"] == 2568
    assert result["features"][:3] == [0.0, 1.0, 2.0]
    assert result["features"][-1] == 2567.0
    assert result["sha256"] == "a" * 64
    assert result["input_kind"] == "pre-extracted-feature-csv"
    assert len(result["source_content_sha256"]) == 64


def test_prepare_lamda_csv_preserves_signed_int8_values() -> None:
    values = [-128, -1, 0, 127] + [1] * 4557
    result = prepare_feature_csv(
        _csv_for("lamda-apk-2022-train-2023-test", values),
        "lamda-apk-2022-train-2023-test",
    )

    assert result["feature_count"] == 4561
    assert result["features"][:4] == [-128.0, -1.0, 0.0, 127.0]


@pytest.mark.parametrize(
    "dataset_id, values, extra_rows",
    [
        ("ember2024-apk", [0.0] * 2567, 0),
        ("ember2024-apk", [0.0] * 2567 + [float("nan")], 0),
        ("ember2024-apk", [0.0] * 2568, 1),
        ("lamda-apk-2022-train-2023-test", [128] + [0] * 4560, 0),
        ("lamda-apk-2022-train-2023-test", [1.5] + [0] * 4560, 0),
    ],
)
def test_prepare_feature_csv_rejects_bad_rows(dataset_id, values, extra_rows) -> None:
    with pytest.raises(ValueError):
        prepare_feature_csv(_csv_for(dataset_id, values, extra_rows=extra_rows), dataset_id)


def test_prepare_feature_csv_rejects_extra_and_missing_columns() -> None:
    names = expected_feature_names("ember2024-apk")
    header = ["sha256", "label", "unexpected", *names]
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(header)
    writer.writerow(["a" * 64, "benign", "not-allowed", *([0.0] * 2568)])

    with pytest.raises(ValueError, match="optional sha256/label"):
        prepare_feature_csv(output.getvalue(), "ember2024-apk")


def test_prepare_feature_csv_rejects_bad_optional_metadata() -> None:
    names = expected_feature_names("ember2024-apk")
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["sha256", "label", *names])
    writer.writerow(["not-a-hash", "benign", *([0.0] * 2568)])

    with pytest.raises(ValueError, match="sha256"):
        prepare_feature_csv(output.getvalue(), "ember2024-apk")


def test_prepare_feature_csv_enforces_one_mib_limit() -> None:
    with pytest.raises(ValueError, match="1 MiB"):
        prepare_feature_csv(" " * (1_048_577), "ember2024-apk")
