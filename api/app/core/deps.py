from fastapi import Header, HTTPException, status

from .security import decode_token


def get_current_user(authorization: str = Header("")) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token"
        )
    token = authorization.split(" ", 1)[1]
    return decode_token(token)
