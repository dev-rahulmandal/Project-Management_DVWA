# =============================================================================
# AUTH-BRUTE-001 - No rate limiting on authentication (credential brute force).
# OWASP A07:2021 | CWE-307 | detector: diver_brute_force
#
# POST /api/auth/login-attempt verifies a password with no throttling, lockout,
# or backoff, so an attacker can try unlimited guesses against an account.
#
# Secured twin AUTH-BRUTE-001-SAFE tracks consecutive failures per account and
# returns 429 once a threshold is reached (cleared on success).
# =============================================================================
import aiosqlite
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ...db import get_db
from ...hardening import hardened

router = APIRouter()


class LoginAttempt(BaseModel):
    email: str
    password: str


async def _verify(db, email: str, password: str) -> bool:
    async with db.execute(
        "SELECT password_hash FROM users WHERE email = ?", (email.strip().lower(),)
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        return False
    try:
        return bcrypt.checkpw(password.encode(), row["password_hash"].encode())
    except ValueError:
        return False


# ---- per-account lockout state (used by the secured path) -------------------
_FAILS: dict[str, int] = {}
_LIMIT = 5


# ---- Two-face: secure path (lockout) vs vulnerable path (unlimited) ----------
@router.post("/api/auth/login-attempt")
async def login_attempt(
    request: Request,
    body: LoginAttempt,
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request):
        # SECURED (negative control): per-account lockout
        email = body.email.strip().lower()
        if _FAILS.get(email, 0) >= _LIMIT:
            raise HTTPException(status_code=429, detail="too_many_attempts")
        if await _verify(db, email, body.password):
            _FAILS.pop(email, None)
            return {"ok": True}
        _FAILS[email] = _FAILS.get(email, 0) + 1
        raise HTTPException(status_code=401, detail="invalid_credentials")
    else:
        # VULNERABLE (intentional): unlimited attempts, no throttling
        if await _verify(db, body.email, body.password):
            return {"ok": True}
        raise HTTPException(status_code=401, detail="invalid_credentials")
