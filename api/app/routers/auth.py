from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..core.security import create_access_token, verify_password, get_password_hash

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(data: LoginRequest):
    # Dummy user validation
    if data.username != "admin" or data.password != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(data.username)
    return {"access_token": token, "token_type": "bearer"}
