#!/usr/bin/env python3
"""Export EMBER2024 vectorized .dat files to bounded detector-ready CSVs."""

import argparse
import json
from pathlib import Path

from nanou_cyber_ai.malware.ember import export_ember_vectorized_subset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--subset", choices=("train", "test"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--max-source-rows",
        type=int,
        default=None,
        help="Maximum source rows to scan (defaults: 2,000 train; 500 test).",
    )
    parser.add_argument("--max-features", type=int, default=4096)
    parser.add_argument("--max-exported-rows", type=int, default=None)
    args = parser.parse_args()
    row_limit = args.max_source_rows
    if row_limit is None:
        row_limit = 2_000 if args.subset == "train" else 500
    report = export_ember_vectorized_subset(
        args.data_dir,
        args.output,
        subset=args.subset,
        max_source_rows=row_limit,
        max_features=args.max_features,
        max_exported_rows=args.max_exported_rows,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
