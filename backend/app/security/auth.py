from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from pydantic import BaseModel

from app.config import EVALUATOR_PASSWORD, EVALUATOR_USERNAME, JWT_EXPIRY_MINUTES, JWT_SECRET_KEY, validate_auth_config

security = HTTPBearer(auto_error=False)
ALGORITHM = "HS256"

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str

def create_jwt_token(username: str) -> str:
    validate_auth_config()
    now = datetime.now(UTC)
    return jwt.encode({"sub": username, "iat": now, "exp": now + timedelta(minutes=JWT_EXPIRY_MINUTES)}, JWT_SECRET_KEY, algorithm=ALGORITHM)

def decode_jwt_token(token: str) -> dict | None:
    validate_auth_config()
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
    except InvalidTokenError:
        return None

def authenticate_user(username: str, password: str) -> str | None:
    validate_auth_config()
    if username.strip().lower() != EVALUATOR_USERNAME.lower() or password != EVALUATOR_PASSWORD:
        return None
    return create_jwt_token(EVALUATOR_USERNAME)

def validate_token(token: str) -> bool:
    return decode_jwt_token(token) is not None

def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> str:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication credentials were not provided", headers={"WWW-Authenticate": "Bearer"})
    payload = decode_jwt_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired authentication token", headers={"WWW-Authenticate": "Bearer"})
    return str(payload["sub"])
