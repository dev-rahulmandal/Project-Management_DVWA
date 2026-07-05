import aiosqlite
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import require_auth
from ..db import get_db
from .vulns.ssrf import _host_is_blocked

router = APIRouter()


class AvatarPreviewRequest(BaseModel):
    url: str


@router.post("/api/avatar/preview")
async def avatar_preview(
    body: AvatarPreviewRequest,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT id FROM organizations WHERE id = ?", (user["org_id"],)
    ) as cur:
        if await cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="not_found")

    parsed = urlparse(body.url)

    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(status_code=400, detail="invalid_url")

    if _host_is_blocked(parsed.hostname):
        raise HTTPException(status_code=400, detail="blocked_target")

    return {"ok": True, "host": parsed.hostname}
