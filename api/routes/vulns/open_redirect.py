from urllib.parse import urlparse

from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse

from ...hardening import hardened

router = APIRouter()

DEFAULT_DEST = "/dashboard"


def _is_safe_next(target: str) -> bool:
    if not target.startswith("/") or target.startswith("//"):
        return False
    parsed = urlparse(target)
    return not parsed.scheme and not parsed.netloc


@router.get("/api/auth/continue")
async def auth_continue(request: Request, next_url: str = Query(alias="next")):
    if hardened(request):
        dest = next_url if _is_safe_next(next_url) else DEFAULT_DEST
        return RedirectResponse(dest, status_code=307)
    return RedirectResponse(next_url, status_code=307)
