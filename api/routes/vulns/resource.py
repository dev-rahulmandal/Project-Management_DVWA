# =============================================================================
# API-RESOURCE-001 - Unrestricted Resource Consumption (no pagination cap).
# OWASP API4:2023 | CWE-770 | detector: diver_resource_consumption
#
# GET /api/events?limit=N honors an arbitrarily large limit with no upper bound,
# so a single request forces the server to build and serialize a huge response
# (memory / CPU / bandwidth) - request limit=10_000_000 to DoS it.
#
# Secured twin API-RESOURCE-001-SAFE clamps the limit to a sane maximum.
# =============================================================================
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
        # ---- SECURED (negative control): limit clamped --------------------
        capped = min(max(limit, 0), MAX_LIMIT)
        return {"count": capped, "events": _events(capped)}
    # ---- VULNERABLE (intentional): limit is unbounded ---------------------
    return {"count": limit, "events": _events(limit)}
