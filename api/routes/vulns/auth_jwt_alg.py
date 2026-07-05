import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ...auth import get_current_user
from ...db import get_db
from ...hardening import hardened

router = APIRouter()
_bearer = HTTPBearer()


def _present(row) -> dict:
    return {
        "id":           row["id"],
        "email":        row["email"],
        "fullName":     row["full_name"],
        "role":         row["role"],
        "orgId":        row["org_id"],
        "isSuperAdmin": bool(row["is_super_admin"]),
    }


async def _user_by_id(db, user_id: int):
    async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cur:
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="user_not_found")
    return row


@router.get("/api/v1/profile", include_in_schema=False)
async def v1_profile(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request):
        user = await get_current_user(credentials=credentials, db=db)
        return {"user": _present(await _user_by_id(db, user["id"]))}

    try:
        claims = jwt.get_unverified_claims(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="invalid_token")

    sub = claims.get("sub")
    if not isinstance(sub, (str, int)):
        raise HTTPException(status_code=401, detail="invalid_token")

    return {"user": _present(await _user_by_id(db, int(sub)))}
