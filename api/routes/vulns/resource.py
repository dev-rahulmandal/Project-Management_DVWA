from fastapi import APIRouter, Depends, Query, Request

from ...auth import require_auth
from ...hardening import hardened

router = APIRouter()

MAX_LIMIT = 100


def _events(n: int) -> list[dict]:
    return [{"id": i, "type": "activity", "message": f"event {i}"} for i in range(n)]


@router.get("/api/events")
async def events(request: Request, limit: int = Query(50), user: dict = Depends(require_auth)):
    if hardened(request):
        capped = min(max(limit, 0), MAX_LIMIT)
        return {"count": capped, "events": _events(capped)}
    return {"count": limit, "events": _events(limit)}
