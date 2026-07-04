"""
Organization member & invitation management (admin area).

This is the SECURE baseline for RBAC - correct ownership/privilege checks
throughout. Intentional privilege-escalation / BFLA / mass-assignment variants
are added later as separate, manifested endpoints; nothing here is a planted vuln.
"""
import secrets
from datetime import datetime, timedelta, timezone

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import require_admin, require_auth
from ..config import config
from ..db import get_db
from .billing import PLANS

router = APIRouter()

_ROLES = ("member", "admin", "owner")
_RANK = {"member": 1, "admin": 2, "owner": 3}
INVITE_TTL_DAYS = 7


def _caller_rank(user: dict) -> int:
    if user.get("is_super_admin"):
        return 99
    return _RANK.get(user["role"], 0)


def present_member(row) -> dict:
    return {
        "id":           row["id"],
        "email":        row["email"],
        "fullName":     row["full_name"],
        "role":         row["role"],
        "isActive":     bool(row["is_active"]),
        "isSuperAdmin": bool(row["is_super_admin"]),
    }


def present_invite(row) -> dict:
    return {
        "id":        row["id"],
        "email":     row["email"],
        "role":      row["role"],
        "expiresAt": row["expires_at"],
        "createdAt": row["created_at"],
    }


def present_org(row) -> dict:
    return {"id": row["id"], "name": row["name"], "slug": row["slug"], "planTier": row["plan_tier"]}


# ------------------------- Org settings --------------------------------------
@router.get("/api/org")
async def get_org(
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT * FROM organizations WHERE id = ?", (user["org_id"],)
    ) as cur:
        row = await cur.fetchone()
    return {"org": present_org(row)}


class OrgUpdate(BaseModel):
    name: str | None = None
    planTier: str | None = None


@router.patch("/api/org")
async def update_org(
    body: OrgUpdate,
    user: dict = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
):
    updates: dict = {}
    if body.name is not None:
        n = body.name.strip()
        if not n:
            raise HTTPException(status_code=400, detail="name_required")
        updates["name"] = n
    if body.planTier is not None:
        if body.planTier not in ("starter", "pro", "enterprise"):
            raise HTTPException(status_code=400, detail="invalid_plan")
        updates["plan_tier"] = body.planTier
    if updates:
        sets = ", ".join(f"{k} = ?" for k in updates)
        await db.execute(
            f"UPDATE organizations SET {sets} WHERE id = ?", [*updates.values(), user["org_id"]]
        )
        await db.commit()
    async with db.execute(
        "SELECT * FROM organizations WHERE id = ?", (user["org_id"],)
    ) as cur:
        row = await cur.fetchone()
    return {"org": present_org(row)}


@router.delete("/api/org")
async def delete_org(
    user: dict = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
):
    # Destructive: owner (or super-admin) only.
    if not user.get("is_super_admin") and user["role"] != "owner":
        raise HTTPException(status_code=403, detail="owner_required")
    org_id = user["org_id"]

    async with db.execute(
        "SELECT stored_name FROM attachments WHERE org_id = ?", (org_id,)
    ) as cur:
        for r in await cur.fetchall():
            try:
                (config.UPLOAD_DIR / r["stored_name"]).unlink(missing_ok=True)
            except OSError:
                pass

    for stmt in (
        "DELETE FROM comments WHERE org_id = ?",
        "DELETE FROM attachments WHERE org_id = ?",
        "DELETE FROM tasks WHERE org_id = ?",
        "DELETE FROM projects WHERE org_id = ?",
        "DELETE FROM invitations WHERE org_id = ?",
        "DELETE FROM audit_logs WHERE org_id = ?",
        "DELETE FROM users WHERE org_id = ?",
        "DELETE FROM organizations WHERE id = ?",
    ):
        await db.execute(stmt, (org_id,))
    await db.commit()
    return {"ok": True}


async def _org_member(db, member_id: int, org_id: int):
    async with db.execute(
        "SELECT * FROM users WHERE id = ? AND org_id = ?", (member_id, org_id)
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")
    return row


# ----------------------------- Members ---------------------------------------
@router.get("/api/org/members")
async def list_members(
    user: dict = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT * FROM users WHERE org_id = ? ORDER BY id", (user["org_id"],)
    ) as cur:
        rows = await cur.fetchall()
    return {"members": [present_member(r) for r in rows]}


class MemberUpdate(BaseModel):
    role: str | None = None
    isActive: bool | None = None


@router.patch("/api/org/members/{member_id}")
async def update_member(
    member_id: int,
    body: MemberUpdate,
    user: dict = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
):
    target = await _org_member(db, member_id, user["org_id"])

    if target["is_super_admin"]:
        raise HTTPException(status_code=403, detail="cannot_modify_superadmin")
    if target["id"] == user["id"]:
        raise HTTPException(status_code=400, detail="cannot_modify_self")

    caller_rank = _caller_rank(user)
    if _RANK.get(target["role"], 0) >= caller_rank:
        raise HTTPException(status_code=403, detail="insufficient_privilege")

    updates: dict = {}
    if body.role is not None:
        if body.role not in _ROLES:
            raise HTTPException(status_code=400, detail="invalid_role")
        if _RANK[body.role] >= caller_rank:           # no granting a role >= your own
            raise HTTPException(status_code=403, detail="cannot_grant_that_role")
        updates["role"] = body.role
    if body.isActive is not None:
        updates["is_active"] = 1 if body.isActive else 0

    if updates:
        sets = ", ".join(f"{k} = ?" for k in updates)
        await db.execute(
            f"UPDATE users SET {sets} WHERE id = ?", [*updates.values(), member_id]
        )
        await db.commit()

    return {"member": present_member(await _org_member(db, member_id, user["org_id"]))}


# --------------------------- Invitations -------------------------------------
class InviteCreate(BaseModel):
    email: str
    role: str = "member"


@router.get("/api/org/invitations")
async def list_invitations(
    user: dict = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT * FROM invitations WHERE org_id = ? ORDER BY id DESC", (user["org_id"],)
    ) as cur:
        rows = await cur.fetchall()
    return {"invitations": [present_invite(r) for r in rows]}


@router.post("/api/org/invitations", status_code=201)
async def create_invitation(
    body: InviteCreate,
    user: dict = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
):
    email = body.email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="invalid_email")

    role = body.role if body.role in ("member", "admin") else "member"
    if role == "admin" and _caller_rank(user) < _RANK["owner"]:
        raise HTTPException(status_code=403, detail="only_owner_can_invite_admin")

    async with db.execute(
        "SELECT 1 FROM users WHERE email = ? AND org_id = ?", (email, user["org_id"])
    ) as cur:
        if await cur.fetchone():
            raise HTTPException(status_code=409, detail="already_member")

    # Seat enforcement: active members + pending invites must stay under the plan limit.
    async with db.execute(
        "SELECT plan_tier FROM organizations WHERE id = ?", (user["org_id"],)
    ) as cur:
        plan = (await cur.fetchone())["plan_tier"]
    limit = PLANS.get(plan, {}).get("seats", 0)
    async with db.execute(
        "SELECT (SELECT COUNT(*) FROM users WHERE org_id = ? AND is_active = 1) "
        "     + (SELECT COUNT(*) FROM invitations WHERE org_id = ?) AS used",
        (user["org_id"], user["org_id"]),
    ) as cur:
        used = (await cur.fetchone())["used"]
    if used >= limit:
        raise HTTPException(status_code=403, detail="seat_limit_reached")

    token = secrets.token_urlsafe(24)
    expires = (datetime.now(timezone.utc) + timedelta(days=INVITE_TTL_DAYS)).isoformat()
    cur = await db.execute(
        "INSERT INTO invitations (org_id, email, role, token, expires_at) VALUES (?, ?, ?, ?, ?)",
        (user["org_id"], email, role, token, expires),
    )
    inv_id = cur.lastrowid
    await db.commit()
    async with db.execute("SELECT * FROM invitations WHERE id = ?", (inv_id,)) as c:
        row = await c.fetchone()
    # token returned so the admin can copy the invite link (real life: emailed).
    return {"invitation": present_invite(row), "token": token}


@router.delete("/api/org/invitations/{invite_id}")
async def revoke_invitation(
    invite_id: int,
    user: dict = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
):
    cur = await db.execute(
        "DELETE FROM invitations WHERE id = ? AND org_id = ?", (invite_id, user["org_id"])
    )
    await db.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="not_found")
    return {"ok": True}
