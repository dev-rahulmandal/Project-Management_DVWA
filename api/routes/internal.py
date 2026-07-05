import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import bcrypt
import aiosqlite
from ..db import get_db

router = APIRouter()


class VerifyRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    fullName: str
    orgName: str


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "org"


@router.post("/api/internal/verify", include_in_schema=False)
async def verify_credentials(
    body: VerifyRequest,
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT * FROM users WHERE email = ?", (body.email,)
    ) as cur:
        row = await cur.fetchone()

    if row is None:
        raise HTTPException(status_code=401, detail="invalid_credentials")

    row_dict = dict(row)
    stored_hash = row_dict.get("password_hash", "")

    if not bcrypt.checkpw(body.password.encode(), stored_hash.encode()):
        raise HTTPException(status_code=401, detail="invalid_credentials")

    if not row_dict.get("is_active", 1):
        raise HTTPException(status_code=403, detail="account_disabled")

    return {
        "id":            row_dict["id"],
        "email":         row_dict["email"],
        "fullName":      row_dict["full_name"],
        "role":          row_dict["role"],
        "orgId":         row_dict["org_id"],
        "isSuperAdmin":  bool(row_dict["is_super_admin"]),
    }


@router.post("/api/internal/register", include_in_schema=False)
async def register_user(
    body: RegisterRequest,
    db: aiosqlite.Connection = Depends(get_db),
):
    email = body.email.strip().lower()
    full_name = body.fullName.strip()
    org_name = body.orgName.strip()

    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="invalid_email")
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="weak_password")
    if not full_name or not org_name:
        raise HTTPException(status_code=400, detail="missing_fields")

    async with db.execute("SELECT 1 FROM users WHERE email = ?", (email,)) as cur:
        if await cur.fetchone() is not None:
            raise HTTPException(status_code=409, detail="email_taken")

    base = _slugify(org_name)
    slug, n = base, 1
    while True:
        async with db.execute(
            "SELECT 1 FROM organizations WHERE slug = ?", (slug,)
        ) as cur:
            if await cur.fetchone() is None:
                break
        n += 1
        slug = f"{base}-{n}"

    org_cur = await db.execute(
        "INSERT INTO organizations (name, slug, plan_tier) VALUES (?, ?, 'starter')",
        (org_name, slug),
    )
    org_id = org_cur.lastrowid

    pw_hash = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt(rounds=12)).decode()
    user_cur = await db.execute(
        "INSERT INTO users (org_id, email, full_name, role, is_super_admin, password_hash) "
        "VALUES (?, ?, ?, 'owner', 0, ?)",
        (org_id, email, full_name, pw_hash),
    )
    user_id = user_cur.lastrowid
    await db.commit()

    return {
        "id":           user_id,
        "email":        email,
        "fullName":     full_name,
        "role":         "owner",
        "orgId":        org_id,
        "isSuperAdmin": False,
    }


class AcceptInviteRequest(BaseModel):
    token: str
    fullName: str
    password: str


@router.post("/api/internal/accept-invite", include_in_schema=False)
async def accept_invite(
    body: AcceptInviteRequest,
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT * FROM invitations WHERE token = ?", (body.token,)
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=400, detail="invalid_token")
    inv = dict(row)

    try:
        exp = datetime.fromisoformat(inv["expires_at"])
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="expired")
    except ValueError:
        pass

    full_name = body.fullName.strip()
    if not full_name or len(body.password) < 8:
        raise HTTPException(status_code=400, detail="invalid_input")

    email = inv["email"].strip().lower()
    async with db.execute("SELECT 1 FROM users WHERE email = ?", (email,)) as cur:
        if await cur.fetchone() is not None:
            raise HTTPException(status_code=409, detail="email_taken")

    pw_hash = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt(rounds=12)).decode()
    user_cur = await db.execute(
        "INSERT INTO users (org_id, email, full_name, role, is_super_admin, password_hash) "
        "VALUES (?, ?, ?, ?, 0, ?)",
        (inv["org_id"], email, full_name, inv["role"], pw_hash),
    )
    user_id = user_cur.lastrowid
    await db.execute("DELETE FROM invitations WHERE id = ?", (inv["id"],))
    await db.commit()

    return {
        "id":           user_id,
        "email":        email,
        "fullName":     full_name,
        "role":         inv["role"],
        "orgId":        inv["org_id"],
        "isSuperAdmin": False,
    }
