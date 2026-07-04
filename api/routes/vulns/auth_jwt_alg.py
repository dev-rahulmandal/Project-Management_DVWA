# =============================================================================
# AUTH-JWT-002 - JWT signature not verified (alg:none / unsigned token accepted).
# OWASP API2:2023 | CWE-347 (Improper Verification of Cryptographic Signature)
# detector: diver_jwt_alg_none
#
# GET /api/v1/profile is a "legacy" reader that pulls claims out of the Bearer
# token with get_unverified_claims() - it NEVER checks the signature. An attacker
# forges an unsigned (alg:none) token with any sub and is trusted as that user.
# This is a different defect from AUTH-JWT-001 (weak shared secret): here NO key
# is needed at all.
#
# Secured twin AUTH-JWT-002-SAFE verifies the signature properly (require_auth).
# =============================================================================
import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ...auth import get_current_user
from ...db import get_db
from ...hardening import hardened

router = APIRouter()
_bearer = HTTPBearer()


def _present(row) -> dict:
    return {
        "id":           row["id"],
        "email":        row["email"],
        "fullName":     row["full_name"],
        "role":         row["role"],
        "orgId":        row["org_id"],
        "isSuperAdmin": bool(row["is_super_admin"]),
    }


async def _user_by_id(db, user_id: int):
    async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cur:
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=401, detail="user_not_found")
    return row


# ---- Two-face reader: one neutral route; behavior chosen at runtime ----------
@router.get("/api/v1/profile")
async def v1_profile(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request):
        # SECURED (negative control): proper signature verification.
        user = await get_current_user(credentials=credentials, db=db)
        return {"user": _present(await _user_by_id(db, user["id"]))}

    # VULNERABLE (intentional): claims trusted with NO signature check.
    try:
        # NO signature verification - an unsigned/alg:none token is accepted.
        claims = jwt.get_unverified_claims(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="invalid_token")

    sub = claims.get("sub")
    if not isinstance(sub, (str, int)):
        raise HTTPException(status_code=401, detail="invalid_token")

    return {"user": _present(await _user_by_id(db, int(sub)))}
