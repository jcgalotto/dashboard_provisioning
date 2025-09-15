from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..core.security import (create_access_token, get_password_hash,
                             verify_password)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


DEMO_USER = "admin"
DEMO_HASH = get_password_hash("admin")


@router.post("/login")
def login(data: LoginRequest):
    if len(data.username) < 3 or len(data.password) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="invalid input"
        )
    if data.username != DEMO_USER or not verify_password(data.password, DEMO_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    token = create_access_token(data.username)
    return {"access_token": token, "token_type": "bearer"}
