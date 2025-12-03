"""Shared security utilities for Pantheon services."""

from passlib.context import CryptContext


_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a bcrypt hash for the given plaintext password."""

    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Validate that ``password`` matches the stored ``password_hash``."""

    return _pwd_context.verify(password, password_hash)
