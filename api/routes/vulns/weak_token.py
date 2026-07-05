import hashlib
import secrets

import aiosqlite
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ...db import get_db
from ...hardening import hardened

router = APIRouter()


class ResetRequest(BaseModel):
    email: str


class ResetConfirm(BaseModel):
    email: str
    token: str
    newPassword: str


def _predictable_token(email: str) -> str:
    return hashlib.md5(email.strip().lower().encode()).hexdigest()


_secure_tokens: dict[str, str] = {}


async def _set_password(db, email: str, new_password: str) -> None:
    pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt(rounds=12)).decode()
    cur = await db.execute(
        "UPDATE users SET password_hash = ? WHERE email = ?",
        (pw_hash, email.strip().lower()),
    )
    await db.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="user_not_found")


@router.post("/api/auth/reset/request")
async def reset_request(request: Request, body: ResetRequest):
    if hardened(request):
        _secure_tokens[body.email.strip().lower()] = secrets.token_urlsafe(32)
        return {"status": "sent"}
    return {"status": "sent"}


@router.post("/api/auth/reset/confirm")
async def reset_confirm(
    request: Request,
    body: ResetConfirm,
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request):
        expected = _secure_tokens.get(body.email.strip().lower())
        if not expected or not secrets.compare_digest(body.token, expected):
            raise HTTPException(status_code=400, detail="invalid_token")
        await _set_password(db, body.email, body.newPassword)
        _secure_tokens.pop(body.email.strip().lower(), None)
        return {"status": "reset"}
    if body.token != _predictable_token(body.email):
        raise HTTPException(status_code=400, detail="invalid_token")
    await _set_password(db, body.email, body.newPassword)
    return {"status": "reset"}
