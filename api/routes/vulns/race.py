import asyncio

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Request

from ...auth import require_auth
from ...config import config
from ...db import get_db
from ...hardening import hardened

router = APIRouter()

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


@router.post("/api/coupons/{code}/redeem")
async def redeem(
    request: Request,
    code: str,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request):
        cur = await db.execute(
            "UPDATE coupons SET remaining_uses = remaining_uses - 1 "
            "WHERE code = ? AND remaining_uses > 0",
            (code,),
        )
        await db.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=400, detail="exhausted")
        return {"redeemed": True}

    async with db.execute(
        "SELECT remaining_uses FROM coupons WHERE code = ?", (code,)
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")
    if row["remaining_uses"] <= 0:
        raise HTTPException(status_code=400, detail="exhausted")

    await asyncio.sleep(0.02)
    await db.execute(
        "UPDATE coupons SET remaining_uses = remaining_uses - 1 WHERE code = ?", (code,)
    )
    await db.commit()
    async with db.execute("SELECT remaining_uses FROM coupons WHERE code = ?", (code,)) as c2:
        r2 = await c2.fetchone()
    if r2 is not None and r2["remaining_uses"] < 0:
        _solve("API-RACE-001")
    return {"redeemed": True}
