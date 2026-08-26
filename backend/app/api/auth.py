from fastapi import APIRouter, HTTPException, status

from app.security.auth import LoginRequest, LoginResponse, authenticate_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    token = authenticate_user(req.username, req.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return LoginResponse(access_token=token, username=req.username)
