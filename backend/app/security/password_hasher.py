"""
GovGuide AI — Password Hashing
Uses bcrypt via passlib. Passwords are NEVER stored in plain text.
"""

from passlib.context import CryptContext

# bcrypt with cost factor 12 (good balance of security and speed)
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    Returns the hashed string to store in the database.
    """
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored bcrypt hash.
    Returns True if the password matches, False otherwise.
    """
    return _pwd_context.verify(plain_password, hashed_password)
