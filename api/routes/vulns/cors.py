# =============================================================================
# API-CORS-001 - Permissive CORS: reflects any Origin with credentials.
# OWASP A05:2021 (Security Misconfiguration) | CWE-942 | detector: diver_cors
#
# GET /api/widget/config hand-rolls CORS and echoes the request Origin straight
# into Access-Control-Allow-Origin while also setting Allow-Credentials: true.
# Reflecting an arbitrary origin together with credentials is the classic
# permissive-CORS misconfiguration scanners flag. (Impact here is limited because
# the API is Bearer-authenticated rather than cookie-authenticated, but the
# misconfiguration - and the detector signal - is real.)
#
# Secured twin API-CORS-001-SAFE reflects only an explicit allowlist of origins.
# =============================================================================
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...hardening import hardened

router = APIRouter()

_ALLOWED = {"http://localhost:8082"}   # the real web origin


def _payload() -> dict:
    return {"orgName": "Acme Corp", "seats": 25, "plan": "pro"}


# ---- VULNERABLE (intentional): reflects ANY origin + credentials ------------
# Runtime-selected behavior: hardened(request) picks the allowlist (secure) path;
# otherwise the request Origin is reflected verbatim (the vuln).
@router.get("/api/widget/config")
async def widget_config(request: Request):
    origin = request.headers.get("origin", "")
    resp = JSONResponse(_payload())
    if hardened(request):
        if origin in _ALLOWED:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
    else:
        if origin:
            resp.headers["Access-Control-Allow-Origin"] = origin   # reflects attacker origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
    return resp
