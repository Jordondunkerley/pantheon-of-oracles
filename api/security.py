"""Shared security utilities for Pantheon services."""

from passlib.context import CryptContext
from passlib.exc import InvalidHash


_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Return a bcrypt hash for the given plaintext password."""

    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Validate that ``password`` matches the stored ``password_hash``."""

    try:
        return _pwd_context.verify(password, password_hash)
    except (ValueError, InvalidHash):
        # Treat malformed or missing hashes as invalid credentials rather than
        # surfacing 500 errors during authentication flows.
        return False


def validate_password_strength(password: str, *, min_length: int = 8) -> None:
    """Raise ``ValueError`` if the password does not meet basic requirements."""

    if len(password) < min_length:
        raise ValueError(f"Password must be at least {min_length} characters long")


def normalize_email(email: str) -> str:
    """Return a trimmed, lowercase email or raise ``ValueError`` if empty."""

    normalized = email.strip().lower()
    if not normalized:
        raise ValueError("Email is required")
    return normalized
