# DECOY (DECOY-SSRF-001) - looks like SSRF but is correctly secured; not a catalogued vuln.
#
# POST /api/avatar/preview takes {"url": "..."} and LOOKS like an SSRF avatar-
# fetcher (the kind a scanner/agent would probe with cloud-metadata or loopback
# URLs). It is intentional benign noise: the url is validated BEFORE any fetch -
# scheme must be http/https and the host must not be internal/loopback/
# link-local/reserved (reusing _host_is_blocked from the real SSRF surface). On
# an allowed public host it does NOT actually fetch (keeps the check offline) and
# just echoes the hostname back. There is no exploitable path here.
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
    # Org-scoped read: confirm the caller's org exists before doing anything.
    # (Keeps every DB access scoped to user["org_id"], like the rest of the app.)
    async with db.execute(
        "SELECT id FROM organizations WHERE id = ?", (user["org_id"],)
    ) as cur:
        if await cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="not_found")

    parsed = urlparse(body.url)

    # SECURE: reject anything that isn't a real http(s) URL with a hostname.
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise HTTPException(status_code=400, detail="invalid_url")

    # SECURE: block internal/loopback/link-local/reserved targets BEFORE any
    # network access. This is what defeats the SSRF the decoy appears to offer.
    if _host_is_blocked(parsed.hostname):
        raise HTTPException(status_code=400, detail="blocked_target")

    # Allowed public host: do NOT fetch (keeps this offline / non-exploitable).
    # Just acknowledge the validated target.
    return {"ok": True, "host": parsed.hostname}
