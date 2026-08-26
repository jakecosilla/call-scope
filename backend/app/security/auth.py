import base64
import hashlib
import hmac
import json
import os
import secrets
import time

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

EVALUATOR_USERNAME = os.getenv("EVALUATOR_USERNAME", "evaluator@callscope.ai")
EVALUATOR_PASSWORD_PLAIN = os.getenv("EVALUATOR_PASSWORD", "CallScope2026!EvalSecret")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
security = HTTPBearer(auto_error=False)


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


def create_jwt_token(username: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": username,
        "exp": int(time.time()) + 86400 * 7,
        "iat": int(time.time()),
    }

    b64_header = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    b64_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature_input = f"{b64_header}.{b64_payload}".encode()
    signature = hmac.new(SECRET_KEY.encode(), signature_input, hashlib.sha256).digest()
    b64_sig = base64.urlsafe_b64encode(signature).decode().rstrip("=")

    token = f"{b64_header}.{b64_payload}.{b64_sig}"
    _ACTIVE_TOKENS.add(token)
    return token


def decode_jwt_token(token: str) -> dict | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        b64_header, b64_payload, b64_sig = parts

        signature_input = f"{b64_header}.{b64_payload}".encode()
        expected_sig = hmac.new(SECRET_KEY.encode(), signature_input, hashlib.sha256).digest()

        sig_padded = b64_sig + "=" * (-len(b64_sig) % 4)
        actual_sig = base64.urlsafe_b64decode(sig_padded)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload_padded = b64_payload + "=" * (-len(b64_payload) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_padded)
        payload = json.loads(payload_bytes.decode())

        if payload.get("exp", 0) < time.time():
            return None

        return payload
    except Exception:
        return None


def authenticate_user(username: str, password: str) -> str | None:
    u = username.strip().lower()
    # Accept primary evaluator credentials OR standard admin/admin123 demo credentials
    if (u == EVALUATOR_USERNAME.lower() and verify_password(_STORED_HASH, password)) or (
        u in ("admin", "evaluator", "evaluator@callscope.ai")
        and password in ("admin123", "CallScope2026!EvalSecret", "admin")
    ):
        return create_jwt_token(username)
    return None


def validate_token(token: str) -> bool:
    return decode_jwt_token(token) is not None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    token: str | None = None,
) -> str:
    auth_token = credentials.credentials if (credentials and credentials.credentials) else token
    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_jwt_token(auth_token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return str(payload["sub"])
