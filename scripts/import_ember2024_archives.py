#!/usr/bin/env python3
"""Download and safely extract EMBER2024 feature-only JSONL archives."""

import argparse
import json
from pathlib import Path

from nanou_cyber_ai.malware.ember_archive import (
    DEFAULT_MAX_UNCOMPRESSED_BYTES,
    safe_extract_ember_archive,
)

REPOSITORY_ID = "joyce8/EMBER2024"
FILE_TYPES = ("Win32", "Win64", "Dot_Net", "APK", "ELF", "PDF")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--subset", choices=("train", "test", "challenge"), required=True)
    parser.add_argument("--file-type", choices=FILE_TYPES, default="APK")
    parser.add_argument(
        "--max-uncompressed-bytes",
        type=int,
        default=DEFAULT_MAX_UNCOMPRESSED_BYTES,
    )
    args = parser.parse_args()

    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise SystemExit(
            'Install the optional downloader dependency: pip install -e ".[ember-download]"'
        ) from exc

    if args.subset == "challenge":
        archive_name = "challenge.zip"
    else:
        archive_name = f"{args.file_type}_{args.subset}.zip"
    archive_path = Path(
        hf_hub_download(
            repo_id=REPOSITORY_ID,
            filename=archive_name,
            repo_type="dataset",
        )
    )
    report = safe_extract_ember_archive(
        archive_path,
        args.data_dir,
        max_uncompressed_bytes=args.max_uncompressed_bytes,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
