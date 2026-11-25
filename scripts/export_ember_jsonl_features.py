#!/usr/bin/env python3
"""Export bounded EMBER2024 JSONL rows with the pinned thrember feature extractor."""

import argparse
import json
from pathlib import Path

from nanou_cyber_ai.malware.ember import export_ember_jsonl_subset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--subset", choices=("train", "test"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-source-rows", type=int, required=True)
    parser.add_argument("--max-exported-rows", type=int, default=None)
    parser.add_argument("--max-features", type=int, default=4096)
    parser.add_argument("--sampling-seed", type=int, default=42)
    args = parser.parse_args()
    report = export_ember_jsonl_subset(
        args.data_dir,
        args.output,
        subset=args.subset,
        max_source_rows=args.max_source_rows,
        max_exported_rows=args.max_exported_rows,
        max_features=args.max_features,
        sampling_seed=args.sampling_seed,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
