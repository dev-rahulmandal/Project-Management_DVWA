# =============================================================================
# API-SSRF-001 - Server-Side Request Forgery via the link-preview feature.
# OWASP API7:2023 | CWE-918 | detector: diver_ssrf
#
# POST /api/projects/{id}/link-preview fetches a user-supplied URL server-side
# (to build a link preview) with NO scheme/host validation. An attacker points
# it at internal-only addresses the server can reach - e.g. the cloud metadata
# service - and the fetched response is handed straight back, leaking internal
# data / credentials.
#
# Local sink: GET /internal/cloud-metadata stands in for the IMDS endpoint
# (169.254.169.254). It is NOT a product route and returns FAKE credentials -
# it exists so the exploit hits a LOCAL sink, never a real external callback
# (per the project safety rules). It is not itself a catalogued vuln; reaching
# it via SSRF is.
#
# Secured twin API-SSRF-001-SAFE rejects non-http(s) schemes and any URL whose
# host resolves to a private / loopback / link-local / reserved address.
# =============================================================================
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
        return True  # unresolvable -> block
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            return True
    return False


# ---- LOCAL SINK: mock cloud metadata (NOT a product route, fake creds) ------
# Answers GET (link-preview SSRF) and POST (webhook-delivery SSRF) alike - the
# real IMDS is GET-only, but accepting POST lets the POST-based webhook delivery
# reach the same recognizable sink.
@router.api_route("/internal/cloud-metadata", methods=["GET", "POST"], include_in_schema=False)
async def mock_cloud_metadata():
    # Simulates the IMDS credentials endpoint an SSRF would target. Fake values.
    return {
        "Code":            "Success",
        "Type":            "AWS-HMAC",
        "AccessKeyId":     "AKIAFAKE_VULNFORGE_SSRF",
        "SecretAccessKey": "fake-secret-do-not-use-training-only",
        "Token":           "FAKE-SESSION-TOKEN",
    }


# ---- TWO-FACE: one neutral route; hardened(request) picks the path ----------
# Vulnerable face (default): fetches any user URL with no scheme/host validation.
# Secure face (hardened): validates scheme + blocks internal/reserved targets.
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
        # SSRF: the user-controlled URL is fetched with no scheme/host checks.
        return await _fetch_preview(body.url)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"fetch_failed: {exc}")
