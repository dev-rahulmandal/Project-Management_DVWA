# =============================================================================
# API-BIZ-SEATS-001 - Seat-quota bypass via bulk invite (BLA7 resource-quota).
# OWASP A04:2021 | CWE-770 | detector: diver_business_logic
#
# The single-invite path (POST /api/org/invitations) enforces the plan seat
# limit. This "bulk invite" path creates invitations with NO seat check, so an
# org already at its limit can invite well beyond it. The secure twin re-applies
# the same seat enforcement to the whole batch.
# =============================================================================
import secrets
from datetime import datetime, timedelta, timezone

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ...auth import require_admin
from ...db import get_db
from ...hardening import hardened
from ..billing import PLANS

router = APIRouter()
INVITE_TTL_DAYS = 7


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


# ---- Seat-quota: one path, behavior chosen at runtime by hardened(request) ---
@router.post("/api/org/invitations/bulk", status_code=201)
async def bulk_invite(
    request: Request,
    body: BulkInvite,
    user: dict = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request):
        # SECURED (negative control): batch seat enforcement
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

    # VULNERABLE (intentional): no seat enforcement
    created = await _create_invites(db, user["org_id"], body.emails)
    return {"created": created, "count": len(created)}
