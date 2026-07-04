# =============================================================================
# API-RACE-001 - TOCTOU race condition on single-use coupon redemption.
# OWASP A04:2021 (Insecure Design) | CWE-362 | detector: diver_race
#
# The redeem flow checks "uses remaining?" and then decrements as two separate
# steps. Concurrent requests all read remaining_uses=1, all pass the guard, then
# all decrement - so a single-use coupon is redeemed many times (double-spend).
# Marked deterministic:false; the test fires many concurrent requests and
# tolerates how many win, asserting only that MORE THAN ONE does.
#
# Secured twin API-RACE-001-SAFE performs an atomic conditional decrement
# (UPDATE ... WHERE remaining_uses > 0), so exactly one concurrent caller wins.
# Both faces live at the one neutral route; hardened(request) selects which runs.
# =============================================================================
import asyncio

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Request

from ...auth import require_auth
from ...db import get_db
from ...hardening import hardened

router = APIRouter()


# ---- Two-face redeem: one neutral route; hardened(request) picks the face -----
@router.post("/api/coupons/{code}/redeem")
async def redeem(
    request: Request,
    code: str,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request):
        # SECURE: atomic conditional decrement - exactly one concurrent winner.
        cur = await db.execute(
            "UPDATE coupons SET remaining_uses = remaining_uses - 1 "
            "WHERE code = ? AND remaining_uses > 0",
            (code,),
        )
        await db.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=400, detail="exhausted")
        return {"redeemed": True}

    # VULNERABLE (intentional): check-then-act, non-atomic.
    async with db.execute(
        "SELECT remaining_uses FROM coupons WHERE code = ?", (code,)
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")
    if row["remaining_uses"] <= 0:
        raise HTTPException(status_code=400, detail="exhausted")

    # TOCTOU window: the guard above and the decrement below are not atomic.
    await asyncio.sleep(0.02)
    await db.execute(
        "UPDATE coupons SET remaining_uses = remaining_uses - 1 WHERE code = ?", (code,)
    )
    await db.commit()
    return {"redeemed": True}
