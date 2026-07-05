from __future__ import annotations

import re
from urllib.parse import urlparse

from fastapi import APIRouter, Request, Response

from ..config import config

try:
    from scoring.store import record_solve as _record_solve
except Exception:
    _record_solve = None

router = APIRouter()

_PROJECT_DETAIL = re.compile(r"^/projects/\d+/?$")


def _solve(vuln_id: str) -> None:
    if config.VF_SCORING and _record_solve is not None:
        try:
            _record_solve(vuln_id, {"surface": "csp-report"})
        except Exception:
            pass


def _map(path: str, directive: str) -> str | None:
    if path.startswith("/secure/"):
        return None
    d = (directive or "").lower()
    if d.startswith("script-src"):
        if _PROJECT_DETAIL.match(path):
            return "WEB-XSS-001"
        if path == "/search":
            return "WEB-DOMXSS-001"
    elif d.startswith("frame-ancestors"):
        return "WEB-CLICKJACK-001"
    return None


def _reports(payload) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    if isinstance(payload, dict) and isinstance(payload.get("csp-report"), dict):
        r = payload["csp-report"]
        out.append((
            r.get("document-uri") or "",
            r.get("effective-directive") or r.get("violated-directive") or "",
            (r.get("disposition") or "").lower(),
        ))
    elif isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict) or item.get("type") != "csp-violation":
                continue
            b = item.get("body") or {}
            out.append((
                b.get("documentURL") or item.get("url") or "",
                b.get("effectiveDirective") or b.get("violatedDirective") or "",
                (b.get("disposition") or "").lower(),
            ))
    return out


@router.post("/api/telemetry/csp")
async def csp_report(request: Request) -> Response:
    try:
        payload = await request.json()
    except Exception:
        payload = None
    for doc_url, directive, disposition in _reports(payload):
        if disposition == "enforce":
            continue
        path = urlparse(doc_url).path or ""
        vuln_id = _map(path, directive)
        if vuln_id:
            _solve(vuln_id)
    return Response(status_code=204)


_CLIENT_EVENT_VULN = {"proto": "WEB-PROTO-001", "clickjack": "WEB-CLICKJACK-001"}


@router.post("/api/telemetry/client")
async def client_event(request: Request) -> Response:
    try:
        payload = await request.json()
    except Exception:
        payload = None
    if isinstance(payload, dict):
        vuln_id = _CLIENT_EVENT_VULN.get(payload.get("t"))
        if vuln_id:
            _solve(vuln_id)
    return Response(status_code=204)
