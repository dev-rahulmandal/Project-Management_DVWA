import aiosqlite
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ...db import get_db
from ...hardening import hardened

router = APIRouter()


class LoginAttempt(BaseModel):
    email: str
    password: str


async def _verify(db, email: str, password: str) -> bool:
    async with db.execute(
        "SELECT password_hash FROM users WHERE email = ?", (email.strip().lower(),)
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        return False
    try:
        return bcrypt.checkpw(password.encode(), row["password_hash"].encode())
    except ValueError:
        return False


_FAILS: dict[str, int] = {}
_LIMIT = 5


@router.post("/api/auth/login-attempt")
async def login_attempt(
    request: Request,
    body: LoginAttempt,
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request):
        email = body.email.strip().lower()
        if _FAILS.get(email, 0) >= _LIMIT:
            raise HTTPException(status_code=429, detail="too_many_attempts")
        if await _verify(db, email, body.password):
            _FAILS.pop(email, None)
            return {"ok": True}
        _FAILS[email] = _FAILS.get(email, 0) + 1
        raise HTTPException(status_code=401, detail="invalid_credentials")
    else:
        if await _verify(db, body.email, body.password):
            return {"ok": True}
        raise HTTPException(status_code=401, detail="invalid_credentials")
