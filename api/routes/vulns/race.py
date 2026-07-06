import asyncio

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Request

from ...auth import require_auth
from ...db import get_db
from ...hardening import hardened

router = APIRouter()


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
    return {"redeemed": True}
