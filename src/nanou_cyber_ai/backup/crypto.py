"""Installed Nanou Cyber Defense AI backup crypto module."""

from __future__ import annotations

import os
import struct
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

_MAGIC = b"NANOUDB1"
_AAD = b"NanouCyberDefenseAI:ProductionBackup:v1"
_NONCE_BYTES = 12
_TAG_BYTES = 16
_KEY_BYTES = 32
_CHUNK_BYTES = 1024 * 1024


def _oaep() -> padding.OAEP:
    return padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=_AAD,
    )


def encrypt_backup(source: Path, public_key_path: Path, destination: Path) -> None:
    """Encrypt a pg_dump file in bounded memory with a random AES data key."""
    public_key = serialization.load_pem_public_key(public_key_path.read_bytes())
    if not isinstance(public_key, rsa.RSAPublicKey) or public_key.key_size < 3072:
        raise ValueError("Backup recipient must be an RSA public key of at least 3072 bits.")

    data_key = os.urandom(_KEY_BYTES)
    nonce = os.urandom(_NONCE_BYTES)
    wrapped_key = public_key.encrypt(data_key, _oaep())
    if len(wrapped_key) > 65535:
        raise ValueError("Wrapped data key is unexpectedly large.")

    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        encryptor = Cipher(algorithms.AES(data_key), modes.GCM(nonce)).encryptor()
        encryptor.authenticate_additional_data(_AAD)
        with source.open("rb") as input_file, os.fdopen(fd, "wb") as output_file:
            output_file.write(_MAGIC)
            output_file.write(struct.pack(">H", len(wrapped_key)))
            output_file.write(wrapped_key)
            output_file.write(nonce)
            while chunk := input_file.read(_CHUNK_BYTES):
                output_file.write(encryptor.update(chunk))
            output_file.write(encryptor.finalize())
            output_file.write(encryptor.tag)
            output_file.flush()
            os.fsync(output_file.fileno())
        os.replace(temporary_path, destination)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise


def decrypt_backup(source: Path, private_key_path: Path, destination: Path) -> None:
    """Authenticate and decrypt a backup using the offline RSA private key."""
    private_key = serialization.load_pem_private_key(
        private_key_path.read_bytes(),
        password=None,
    )
    if not isinstance(private_key, rsa.RSAPrivateKey) or private_key.key_size < 3072:
        raise ValueError("Backup private key must be RSA with at least 3072 bits.")

    file_size = source.stat().st_size
    with source.open("rb") as input_file:
        if input_file.read(len(_MAGIC)) != _MAGIC:
            raise ValueError("Unrecognized Nanou backup file format.")
        raw_length = input_file.read(2)
        if len(raw_length) != 2:
            raise ValueError("Backup header is truncated.")
        wrapped_length = struct.unpack(">H", raw_length)[0]
        wrapped_key = input_file.read(wrapped_length)
        nonce = input_file.read(_NONCE_BYTES)
        ciphertext_offset = len(_MAGIC) + 2 + wrapped_length + _NONCE_BYTES
        ciphertext_length = file_size - ciphertext_offset - _TAG_BYTES
        if len(wrapped_key) != wrapped_length or len(nonce) != _NONCE_BYTES:
            raise ValueError("Backup header is truncated.")
        if ciphertext_length < 0:
            raise ValueError("Backup file is truncated.")

        input_file.seek(file_size - _TAG_BYTES)
        tag = input_file.read(_TAG_BYTES)
        if len(tag) != _TAG_BYTES:
            raise ValueError("Backup authentication tag is missing.")

        data_key = private_key.decrypt(wrapped_key, _oaep())
        if len(data_key) != _KEY_BYTES:
            raise ValueError("Unwrapped backup key has an invalid length.")

        decryptor = Cipher(algorithms.AES(data_key), modes.GCM(nonce, tag)).decryptor()
        decryptor.authenticate_additional_data(_AAD)
        input_file.seek(ciphertext_offset)

        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=destination.parent,
        )
        temporary_path = Path(temporary_name)
        remaining = ciphertext_length
        try:
            with os.fdopen(fd, "wb") as output_file:
                while remaining:
                    chunk = input_file.read(min(_CHUNK_BYTES, remaining))
                    if not chunk:
                        raise ValueError("Backup ciphertext is truncated.")
                    remaining -= len(chunk)
                    output_file.write(decryptor.update(chunk))
                output_file.write(decryptor.finalize())
                output_file.flush()
                os.fsync(output_file.fileno())
            os.replace(temporary_path, destination)
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise
