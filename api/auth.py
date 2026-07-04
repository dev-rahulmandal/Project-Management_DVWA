import aiosqlite
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from .config import config
from .db import get_db

_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET,
            algorithms=["HS256"],
            issuer=config.JWT_ISSUER,
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="invalid_token")

    user_id = payload.get("sub")
    if not isinstance(user_id, (str, int)):
        raise HTTPException(status_code=401, detail="invalid_token")

    async with db.execute("SELECT * FROM users WHERE id = ?", (int(user_id),)) as cur:
        row = await cur.fetchone()

    if row is None:
        raise HTTPException(status_code=401, detail="user_not_found")

    user = dict(row)
    if not user.get("is_active", 1):
        raise HTTPException(status_code=403, detail="account_disabled")

    return user


# Alias used in route files for clarity
require_auth = get_current_user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if not user["is_super_admin"] and user["role"] not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="forbidden")
    return user
