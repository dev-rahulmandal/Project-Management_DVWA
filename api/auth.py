import hashlib

import aiosqlite
from fastapi import Depends, HTTPException, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from .config import config
from .db import get_db

_bearer = HTTPBearer()

# Personal access tokens (vfpat_) are scoped to these API resource prefixes.
_PAT_RESOURCE = {"me": "profile", "projects": "projects", "tasks": "tasks"}


def _pat_scope_ok(method: str, path: str, scopes: list) -> bool:
    parts = [p for p in path.split("/") if p]
    if len(parts) < 2 or parts[0] != "api":
        return False
    resource = _PAT_RESOURCE.get(parts[1])
    if resource is None:
        return False
    access = "read" if method in ("GET", "HEAD", "OPTIONS") else "write"
    return (f"{resource}:{access}" in scopes
            or (access == "read" and f"{resource}:write" in scopes))


async def _user_from_pat(request: Request, token: str, db) -> dict:
    async with db.execute(
        "SELECT * FROM api_keys WHERE token_hash = ?",
        (hashlib.sha256(token.encode()).hexdigest(),),
    ) as cur:
        key = await cur.fetchone()
    if key is None:
        raise HTTPException(status_code=401, detail="invalid_key")
    if not _pat_scope_ok(request.method, request.url.path, (key["scopes"] or "").split()):
        raise HTTPException(status_code=403, detail="insufficient_scope")
    async with db.execute("SELECT * FROM users WHERE id = ?", (key["user_id"],)) as cur:
        row = await cur.fetchone()
    if row is None or not row["is_active"]:
        raise HTTPException(status_code=401, detail="invalid_key")
    return dict(row)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    token = credentials.credentials

    if token.startswith("vfpat_"):
        return await _user_from_pat(request, token, db)

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


require_auth = get_current_user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if not user["is_super_admin"] and user["role"] not in ("admin", "owner"):
        raise HTTPException(status_code=403, detail="forbidden")
    return user
