# =============================================================================
# AUTH-REDIRECT-001 - Open Redirect on the post-login "continue" endpoint.
# OWASP A01:2021 | CWE-601 | detector: diver_open_redirect
#
# GET /api/auth/continue?next=<url> is the "bounce the user back to where they
# were going after auth" endpoint (the OAuth redirect_uri pattern). It issues a
# redirect to the user-supplied `next` with NO validation, so an attacker can
# craft a link on this trusted origin that forwards victims to a phishing site.
# Unauthenticated on purpose - the phishing value is the trusted-origin bounce.
#
# Secured twin AUTH-REDIRECT-001-SAFE only honors same-origin RELATIVE paths and
# otherwise falls back to a safe default destination.
# =============================================================================
from urllib.parse import urlparse

from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse

from ...hardening import hardened

router = APIRouter()

DEFAULT_DEST = "/dashboard"


def _is_safe_next(target: str) -> bool:
    # Same-origin relative paths only: must start with a single "/", and carry
    # no scheme or host. Rejects "//evil.com", "https://evil.com", "javascript:".
    if not target.startswith("/") or target.startswith("//"):
        return False
    parsed = urlparse(target)
    return not parsed.scheme and not parsed.netloc


# ---- Two-face route: one neutrally-named path, behavior chosen at runtime ----
@router.get("/api/auth/continue")
async def auth_continue(request: Request, next_url: str = Query(alias="next")):
    if hardened(request):
        # SECURED (negative control): allowlist relative paths only.
        dest = next_url if _is_safe_next(next_url) else DEFAULT_DEST
        return RedirectResponse(dest, status_code=307)
    # VULNERABLE (intentional): open redirect, no validation of the destination.
    return RedirectResponse(next_url, status_code=307)
