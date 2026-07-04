# =============================================================================
# AUTH-RESET-001 - Predictable password-reset token (insecure randomness).
# OWASP A02:2021 (Cryptographic Failures) | CWE-330 | detector: diver_weak_token
#
# The reset token is a pure function of the (public) email - md5(email) - so an
# attacker who knows a victim's email computes the token and resets the victim's
# password, taking over the account. No secret, no interception needed.
#
# Secured twin AUTH-RESET-001-SAFE issues a cryptographically-random token at
# request time, stores it, and constant-time-compares it at confirm - a guessed
# md5(email) is rejected.
# =============================================================================
import hashlib
import secrets

import aiosqlite
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ...db import get_db
from ...hardening import hardened

router = APIRouter()


class ResetRequest(BaseModel):
    email: str


class ResetConfirm(BaseModel):
    email: str
    token: str
    newPassword: str


def _predictable_token(email: str) -> str:
    # INSECURE: token derivable from a public value.
    return hashlib.md5(email.strip().lower().encode()).hexdigest()


# Secure twin's store: email -> random token (single process; fine for training).
_secure_tokens: dict[str, str] = {}


async def _set_password(db, email: str, new_password: str) -> None:
    pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt(rounds=12)).decode()
    cur = await db.execute(
        "UPDATE users SET password_hash = ? WHERE email = ?",
        (pw_hash, email.strip().lower()),
    )
    await db.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="user_not_found")


# ---- TWO-FACE: one route; hardened(request) picks secure vs. vulnerable -----
@router.post("/api/auth/reset/request")
async def reset_request(request: Request, body: ResetRequest):
    if hardened(request):
        # SECURE: issue + store a cryptographically-random token.
        _secure_tokens[body.email.strip().lower()] = secrets.token_urlsafe(32)
        return {"status": "sent"}
    # VULNERABLE: production would email _predictable_token(body.email) - md5(email).
    return {"status": "sent"}


@router.post("/api/auth/reset/confirm")
async def reset_confirm(
    request: Request,
    body: ResetConfirm,
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request):
        # SECURE: random token, stored + constant-time-compared.
        expected = _secure_tokens.get(body.email.strip().lower())
        if not expected or not secrets.compare_digest(body.token, expected):
            raise HTTPException(status_code=400, detail="invalid_token")
        await _set_password(db, body.email, body.newPassword)
        _secure_tokens.pop(body.email.strip().lower(), None)
        return {"status": "reset"}
    # VULNERABLE: token == md5(email), derivable from a public value.
    if body.token != _predictable_token(body.email):
        raise HTTPException(status_code=400, detail="invalid_token")
    await _set_password(db, body.email, body.newPassword)
    return {"status": "reset"}
