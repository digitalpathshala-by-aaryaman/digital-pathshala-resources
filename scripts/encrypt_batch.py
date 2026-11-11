#!/usr/bin/env python3
"""Encrypt a video resource batch locally BEFORE uploading it to this public repo."""
import os
import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python scripts/encrypt_batch.py INPUT.zip vault/batch-002.zip.enc")
    if len(os.getenv("DP_VAULT_PASSPHRASE", "")) < 28:
        raise SystemExit("Set a strong DP_VAULT_PASSPHRASE (28+ chars); never commit it.")
    target = Path(sys.argv[2])
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt", "-iter", "200000",
         "-in", sys.argv[1], "-out", str(target), "-pass", "env:DP_VAULT_PASSPHRASE"],
        check=True
    )
    print("Encrypted batch ready:", target, "size:", target.stat().st_size)
