import ipaddress
import socket
from urllib.parse import urlparse

import aiosqlite
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ...auth import require_auth
from ...db import get_db
from ...hardening import hardened

router = APIRouter()

FETCH_TIMEOUT = 5.0
MAX_PREVIEW_BYTES = 2048


class LinkPreviewRequest(BaseModel):
    url: str


async def _require_org_project(db, project_id: int, org_id: int) -> None:
    async with db.execute(
        "SELECT id FROM projects WHERE id = ? AND org_id = ?", (project_id, org_id)
    ) as cur:
        if await cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="not_found")


async def _fetch_preview(url: str) -> dict:
    async with httpx.AsyncClient(timeout=FETCH_TIMEOUT, follow_redirects=False) as client:
        r = await client.get(url)
    return {
        "status":      r.status_code,
        "contentType": r.headers.get("content-type"),
        "body":        r.text[:MAX_PREVIEW_BYTES],
    }


def _host_is_blocked(host: str) -> bool:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return True
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            return True
    return False


@router.api_route("/internal/cloud-metadata", methods=["GET", "POST"], include_in_schema=False)
async def mock_cloud_metadata():
    return {
        "Code":            "Success",
        "Type":            "AWS-HMAC",
        "AccessKeyId":     "ASIA5J7KQP2XR8VNZW3T",
        "SecretAccessKey": "hK9vB2nQ7pR4tW8xZ1cF6dS3gY5jL0mNqAe2uH4p",
        "Token":           "FQoGZXIvYXdzEJr3g8Lk9wEaDN2xK7mQ4pR8tW1cZyK8Ax0vB5nH3jL6dS9gY2fF4uH7pR",
    }


@router.post("/api/projects/{project_id}/link-preview")
async def link_preview(
    request: Request,
    project_id: int,
    body: LinkPreviewRequest,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    await _require_org_project(db, project_id, user["org_id"])
    if hardened(request):
        parsed = urlparse(body.url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise HTTPException(status_code=400, detail="invalid_url")
        if _host_is_blocked(parsed.hostname):
            raise HTTPException(status_code=400, detail="blocked_target")
        try:
            return await _fetch_preview(body.url)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"fetch_failed: {exc}")
    try:
        return await _fetch_preview(body.url)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"fetch_failed: {exc}")
