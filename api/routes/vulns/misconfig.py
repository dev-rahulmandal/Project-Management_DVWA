# =============================================================================
# API-MISCONFIG-001 - Security misconfiguration: debug endpoint left enabled.
# OWASP API8:2023 | CWE-489 (Active Debug Code) | detector: diver_misconfig
#
# GET /api/debug/config is a diagnostics route that was never disabled. It is
# UNAUTHENTICATED and dumps server configuration - including the JWT signing
# secret - which an attacker uses to forge tokens (chains into AUTH-JWT-001).
#
# Secured twin API-MISCONFIG-001-SAFE is admin-gated AND redacts secrets, so
# even an authorized admin never sees the signing key.
# =============================================================================
import os
import sys

import aiosqlite
from fastapi import APIRouter, Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ...auth import get_current_user, require_admin
from ...config import config
from ...db import get_db
from ...hardening import hardened

router = APIRouter()

# Optional bearer so the unhardened (vulnerable) path stays UNAUTHENTICATED while
# the hardened path can still admin-gate. require_admin can't be a route-level
# dependency here: it would force auth on the open debug route and the vuln would
# never fire.
_optional_bearer = HTTPBearer(auto_error=False)


# ---- VULNERABLE (intentional): open debug route, leaks secrets --------------
# Behavior is chosen at runtime by hardened(request): when hardened, the route is
# admin-gated AND redacts secrets (the negative control); otherwise it is the
# open, unauthenticated debug route that leaks the JWT signing secret.
@router.get("/api/debug/config")
async def debug_config(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(_optional_bearer),
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request):
        # SECURED (negative control): admin-gated + redacted. Resolve the caller
        # inline (require_admin chained from get_current_user) so the gate only
        # applies on this branch.
        user = await get_current_user(credentials=credentials, db=db)
        user = await require_admin(user=user)
        return {
            "jwtIssuer": config.JWT_ISSUER,
            "webOrigin": config.WEB_ORIGIN,
            "jwtSecret": "***redacted***",
        }
    return {
        "jwtSecret":     config.JWT_SECRET,          # signing key leaked
        "jwtIssuer":     config.JWT_ISSUER,
        "dbPath":        str(config.DB_PATH),
        "webOrigin":     config.WEB_ORIGIN,
        "pythonVersion": sys.version.split()[0],
        "env": {
            k: v for k, v in os.environ.items()
            if k.startswith(("JWT_", "DATABASE_", "SESSION_"))
        },
    }
