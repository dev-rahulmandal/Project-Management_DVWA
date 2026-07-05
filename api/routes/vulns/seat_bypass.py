import secrets
from datetime import datetime, timedelta, timezone

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ...auth import require_admin
from ...config import config
from ...db import get_db
from ...hardening import hardened
from ..billing import PLANS

router = APIRouter()
INVITE_TTL_DAYS = 7

try:
    from scoring.store import record_solve as _record_solve
except Exception:
    _record_solve = None


def _solve(vuln_id: str) -> None:
    if config.VF_SCORING and _record_solve is not None:
        try:
            _record_solve(vuln_id, {"surface": "http-hook"})
        except Exception:
            pass


class BulkInvite(BaseModel):
    emails: list[str]


async def _create_invites(db, org_id: int, emails: list[str]) -> list[str]:
    created = []
    for raw in emails:
        email = raw.strip().lower()
        if "@" not in email:
            continue
        async with db.execute(
            "SELECT 1 FROM users WHERE email = ? AND org_id = ?", (email, org_id)
        ) as c:
            if await c.fetchone():
                continue
        token = secrets.token_urlsafe(24)
        expires = (datetime.now(timezone.utc) + timedelta(days=INVITE_TTL_DAYS)).isoformat()
        await db.execute(
            "INSERT INTO invitations (org_id, email, role, token, expires_at) VALUES (?, ?, 'member', ?, ?)",
            (org_id, email, token, expires),
        )
        created.append(email)
    await db.commit()
    return created


async def _seats_used(db, org_id: int) -> int:
    async with db.execute(
        "SELECT (SELECT COUNT(*) FROM users WHERE org_id = ? AND is_active = 1) "
        "     + (SELECT COUNT(*) FROM invitations WHERE org_id = ?) AS used",
        (org_id, org_id),
    ) as c:
        return (await c.fetchone())["used"]


async def _maybe_solve_seats(db, org_id: int, created_count: int) -> None:
    if created_count == 0 or not (config.VF_SCORING and _record_solve is not None):
        return
    try:
        async with db.execute(
            "SELECT plan_tier FROM organizations WHERE id = ?", (org_id,)
        ) as c:
            plan = (await c.fetchone())["plan_tier"]
        limit = PLANS.get(plan, {}).get("seats", 0)
        if await _seats_used(db, org_id) > limit:
            _solve("API-BIZ-SEATS-001")
    except Exception:
        pass


@router.post("/api/org/invitations/bulk", status_code=201)
async def bulk_invite(
    request: Request,
    body: BulkInvite,
    user: dict = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request):
        async with db.execute(
            "SELECT plan_tier FROM organizations WHERE id = ?", (user["org_id"],)
        ) as c:
            plan = (await c.fetchone())["plan_tier"]
        limit = PLANS.get(plan, {}).get("seats", 0)
        valid = [e for e in body.emails if "@" in e]
        if await _seats_used(db, user["org_id"]) + len(valid) > limit:
            raise HTTPException(status_code=403, detail="seat_limit_reached")
        created = await _create_invites(db, user["org_id"], valid)
        return {"created": created, "count": len(created)}

    created = await _create_invites(db, user["org_id"], body.emails)
    await _maybe_solve_seats(db, user["org_id"], len(created))
    return {"created": created, "count": len(created)}
