from fastapi import APIRouter, Depends, Request

from ..auth import require_auth

router = APIRouter()

_ALLOWED_PREF_KEYS = ("theme", "language", "timezone")


@router.patch("/api/me/preferences")
async def update_preferences(
    request: Request,
    user: dict = Depends(require_auth),
):
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}

    accepted = {key: body[key] for key in _ALLOWED_PREF_KEYS if key in body}

    return {"preferences": accepted}
