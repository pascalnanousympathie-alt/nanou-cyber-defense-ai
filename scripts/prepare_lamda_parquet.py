#!/usr/bin/env python3
"""Validate and convert pinned LAMDA APK Parquet splits to bounded feature CSVs."""

import argparse
import json
from pathlib import Path

from nanou_cyber_ai.malware.lamda import prepare_lamda_parquet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-parquet", type=Path, required=True)
    parser.add_argument("--test-parquet", type=Path, required=True)
    parser.add_argument("--train-csv", type=Path, required=True)
    parser.add_argument("--test-csv", type=Path, required=True)
    parser.add_argument("--report-json", type=Path, required=True)
    parser.add_argument("--max-train-rows", type=int, default=10_000)
    parser.add_argument("--max-test-rows", type=int, default=12_000)
    parser.add_argument("--sampling-seed", type=int, default=42)
    args = parser.parse_args()
    report_path = args.report_json.expanduser()
    if report_path.exists():
        raise FileExistsError(f"Refusing to overwrite report: {report_path}")
    csv_paths = {
        args.train_csv.expanduser().resolve(),
        args.test_csv.expanduser().resolve(),
    }
    if len(csv_paths) != 2 or report_path.resolve() in csv_paths:
        raise ValueError("Report, train CSV and test CSV paths must be different.")

    report = prepare_lamda_parquet(
        args.train_parquet,
        args.test_parquet,
        args.train_csv,
        args.test_csv,
        max_train_rows=args.max_train_rows,
        max_test_rows=args.max_test_rows,
        sampling_seed=args.sampling_seed,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
