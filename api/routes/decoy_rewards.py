import asyncio

from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_auth

router = APIRouter()

_REWARDS = {"LOYALTY5": 1, "EARLYBIRD": 1, "REFER10": 1}
_LOCK = asyncio.Lock()


@router.post("/api/rewards/{code}/claim")
async def claim_reward(code: str, user: dict = Depends(require_auth)):
    async with _LOCK:
        remaining = _REWARDS.get(code)
        if remaining is None:
            raise HTTPException(status_code=404, detail="unknown_reward")
        if remaining <= 0:
            raise HTTPException(status_code=409, detail="already_claimed")
        _REWARDS[code] = remaining - 1
    return {"claimed": True, "code": code}
