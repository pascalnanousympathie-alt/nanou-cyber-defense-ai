"""Argon2id password hashing helpers."""

from __future__ import annotations

import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_hasher = PasswordHasher(time_cost=3, memory_cost=65_536, parallelism=2, hash_len=32, salt_len=16)

_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(32))


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, encoded_hash: str | None) -> bool:
    target_hash = encoded_hash or _DUMMY_HASH
    try:
        result = _hasher.verify(target_hash, password)
        return result and encoded_hash is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
