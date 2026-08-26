import hashlib
import hmac
import os
import secrets

from pydantic import BaseModel

EVALUATOR_USERNAME = os.getenv("EVALUATOR_USERNAME", "evaluator@callscope.ai")
EVALUATOR_PASSWORD_PLAIN = os.getenv("EVALUATOR_PASSWORD", "CallScope2026!EvalSecret")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return salt.hex() + ":" + key.hex()


def verify_password(stored_password_hash: str, provided_password: str) -> bool:
    try:
        salt_hex, key_hex = stored_password_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        key = hashlib.pbkdf2_hmac("sha256", provided_password.encode("utf-8"), salt, 100000)
        return hmac.compare_digest(key, expected_key)
    except Exception:
        return False


_STORED_HASH = hash_password(EVALUATOR_PASSWORD_PLAIN)
_ACTIVE_TOKENS: set[str] = set()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str


def authenticate_user(username: str, password: str) -> str | None:
    if username.strip().lower() == EVALUATOR_USERNAME.lower() and verify_password(_STORED_HASH, password):
        token = secrets.token_urlsafe(32)
        _ACTIVE_TOKENS.add(token)
        return token
    return None


def validate_token(token: str) -> bool:
    return token in _ACTIVE_TOKENS
