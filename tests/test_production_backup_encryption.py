from __future__ import annotations

import os
from pathlib import Path

import pytest
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from scripts.production_backup_crypto import decrypt_backup, encrypt_backup


def make_rsa_keypair(directory: Path, *, bits: int = 3072) -> tuple[Path, Path]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=bits)
    private_path = directory / "private.pem"
    public_path = directory / "public.pem"
    private_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    public_path.write_bytes(
        private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return private_path, public_path


def test_production_backup_streaming_round_trip(tmp_path: Path) -> None:
    private_key, public_key = make_rsa_keypair(tmp_path)
    source = tmp_path / "production.dump"
    encrypted = tmp_path / "production.dump.ncdb"
    restored = tmp_path / "restored.dump"
    source.write_bytes(os.urandom(2 * 1024 * 1024 + 37))

    encrypt_backup(source, public_key, encrypted)
    assert encrypted.read_bytes().startswith(b"NANOUDB1")
    assert encrypted.stat().st_size > source.stat().st_size

    decrypt_backup(encrypted, private_key, restored)
    assert restored.read_bytes() == source.read_bytes()


def test_production_backup_rejects_tampering_and_removes_partial_output(tmp_path: Path) -> None:
    private_key, public_key = make_rsa_keypair(tmp_path)
    source = tmp_path / "production.dump"
    encrypted = tmp_path / "production.dump.ncdb"
    restored = tmp_path / "restored.dump"
    source.write_bytes(b"production-data-sample")

    encrypt_backup(source, public_key, encrypted)
    damaged = bytearray(encrypted.read_bytes())
    damaged[-1] ^= 0x01
    encrypted.write_bytes(damaged)

    with pytest.raises(InvalidTag):
        decrypt_backup(encrypted, private_key, restored)

    assert not restored.exists()
    assert not list(tmp_path.glob(".restored.dump.*.tmp"))


def test_production_backup_rejects_short_rsa_key(tmp_path: Path) -> None:
    _, short_public = make_rsa_keypair(tmp_path, bits=2048)
    source = tmp_path / "production.dump"
    source.write_bytes(b"sample")

    with pytest.raises(ValueError, match="at least 3072 bits"):
        encrypt_backup(source, short_public, tmp_path / "backup.ncdb")
