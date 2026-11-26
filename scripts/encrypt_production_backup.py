from __future__ import annotations

import argparse
from pathlib import Path

from scripts.production_backup_crypto import encrypt_backup


def main() -> int:
    parser = argparse.ArgumentParser(description="Encrypt a Nanou Production PostgreSQL dump.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--public-key", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    encrypt_backup(args.input, args.public_key, args.output)
    print(f"Encrypted Production backup written: {args.output.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
