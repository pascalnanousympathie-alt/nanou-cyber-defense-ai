from __future__ import annotations

import argparse
from pathlib import Path

from nanou_cyber_ai.backup.crypto import decrypt_backup


def main() -> int:
    parser = argparse.ArgumentParser(description="Decrypt a Nanou Production backup.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--private-key", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    decrypt_backup(args.input, args.private_key, args.output)
    print(f"Authenticated Production backup restored to: {args.output.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
