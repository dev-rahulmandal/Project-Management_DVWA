import aiosqlite
import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import require_auth
from ..db import get_db

router = APIRouter()


@router.get("/api/me")
async def get_me(user: dict = Depends(require_auth)):
    return {
        "id": user["id"],
        "email": user["email"],
        "fullName": user["full_name"],
        "role": user["role"],
        "orgId": user["org_id"],
        "isSuperAdmin": bool(user["is_super_admin"]),
    }


class PasswordChange(BaseModel):
    currentPassword: str
    newPassword: str


@router.post("/api/me/password")
async def change_password(
    body: PasswordChange,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT password_hash FROM users WHERE id = ?", (user["id"],)
    ) as cur:
        row = await cur.fetchone()
    try:
        ok = bcrypt.checkpw(body.currentPassword.encode(), row["password_hash"].encode())
    except ValueError:
        ok = False
    if not ok:
        raise HTTPException(status_code=400, detail="wrong_current_password")
    if len(body.newPassword) < 8:
        raise HTTPException(status_code=400, detail="weak_password")
    new_hash = bcrypt.hashpw(body.newPassword.encode(), bcrypt.gensalt(rounds=12)).decode()
    await db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user["id"]))
    await db.commit()
    return {"ok": True}
