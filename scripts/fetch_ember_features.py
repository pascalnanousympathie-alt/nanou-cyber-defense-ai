#!/usr/bin/env python3
"""Download EMBER 2018's feature archive and verify its upstream SHA-256.

The archive contains pre-extracted static features, not executable PE samples.
No malware binaries are downloaded or executed by this script.
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from pathlib import Path

URL = "https://ember.elastic.co/ember_dataset_2018_2.tar.bz2"
EXPECTED_SHA256 = "b6052eb8d350a49a8d5a5396fbe7d16cf42848b86ff969b77464434cf2997812"
TARGET = Path("datasets/cache/ember_dataset_2018_2.tar.bz2")
MAX_BYTES = 8 * 1024 * 1024 * 1024


def main() -> int:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    total = 0
    temporary = TARGET.with_suffix(TARGET.suffix + ".part")
    try:
        request = urllib.request.Request(URL, headers={"User-Agent": "NanouCyberDefenseAI/0.1"})
        with (
            urllib.request.urlopen(request, timeout=30) as response,
            temporary.open("wb") as output,
        ):
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_BYTES:
                    raise ValueError("Archive exceeds the 8 GiB safety limit")
                digest.update(chunk)
                output.write(chunk)
        actual = digest.hexdigest()
        if actual != EXPECTED_SHA256:
            raise ValueError(f"SHA-256 mismatch: got {actual}")
        temporary.replace(TARGET)
        print(f"Verified static-feature archive: {TARGET} ({total} bytes)")
        return 0
    except Exception as exc:
        temporary.unlink(missing_ok=True)
        print(f"Download/verification failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
