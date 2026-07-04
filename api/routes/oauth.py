"""
OAuth2 / OIDC authorization server (secure baseline).

Authorization-code flow with PKCE:
  POST /api/oauth/authorize  (the logged-in user authorizes a client)
  POST /api/oauth/token      (exchange a single-use code for tokens)
  GET  /api/oauth/userinfo   (OIDC claims for an access token)
  GET  /api/oauth/.well-known/openid-configuration

Secure properties: redirect_uri must EXACTLY match the client's registered
allowlist; auth codes are single-use, short-lived, and bound to the client +
redirect_uri; PKCE (S256) is verified; confidential clients need their secret.
Intentional variants (DCR SSRF, loose redirect_uri matching, PKCE downgrade)
are added later as separate, manifested endpoints.
"""
import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Request
from jose import jwt
from pydantic import BaseModel

from ..auth import require_auth
from ..config import config
from ..db import get_db
from ..hardening import hardened
from ..oauth_keys import JWKS, KID, PRIVATE_PEM

router = APIRouter()

CODE_TTL = 300
TOKEN_TTL = 3600


def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _verify_pkce(verifier: str, challenge: str, method: str | None) -> bool:
    if (method or "S256") == "S256":
        return _b64url(hashlib.sha256(verifier.encode()).digest()) == challenge
    return verifier == challenge


async def _client(db, client_id: str):
    async with db.execute(
        "SELECT * FROM oauth_clients WHERE client_id = ?", (client_id,)
    ) as c:
        return await c.fetchone()


def _ts(seconds: int) -> int:
    return int((datetime.now(timezone.utc) + timedelta(seconds=seconds)).timestamp())


class AuthorizeRequest(BaseModel):
    clientId: str
    redirectUri: str
    scope: str = "openid profile"
    state: str | None = None
    codeChallenge: str | None = None
    codeChallengeMethod: str | None = "S256"


@router.post("/api/oauth/authorize")
async def authorize(
    request: Request,
    body: AuthorizeRequest,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    client = await _client(db, body.clientId)
    if client is None:
        raise HTTPException(status_code=400, detail="invalid_client")
    allowed = client["redirect_uris"].split()
    if hardened(request):
        ok = body.redirectUri in allowed                          # EXACT allowlist match
    else:
        # AUTH-OAUTH-REDIR-001 (default): substring match - any URL that merely
        # CONTAINS a registered value passes, so the real host can be the attacker's.
        ok = any(a in body.redirectUri for a in allowed)
    if not ok:
        raise HTTPException(status_code=400, detail="invalid_redirect_uri")

    code = secrets.token_urlsafe(24)
    await db.execute(
        "INSERT INTO oauth_codes "
        "(code, client_id, user_id, redirect_uri, scope, code_challenge, code_challenge_method, expires_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (code, body.clientId, user["id"], body.redirectUri, body.scope,
         body.codeChallenge, body.codeChallengeMethod,
         (datetime.now(timezone.utc) + timedelta(seconds=CODE_TTL)).isoformat()),
    )
    await db.commit()
    return {"code": code, "state": body.state, "redirectUri": body.redirectUri}


class TokenRequest(BaseModel):
    grantType: str = "authorization_code"
    code: str
    clientId: str
    clientSecret: str | None = None
    codeVerifier: str | None = None
    redirectUri: str


@router.post("/api/oauth/token")
async def token(
    request: Request,
    body: TokenRequest,
    db: aiosqlite.Connection = Depends(get_db),
):
    if body.grantType != "authorization_code":
        raise HTTPException(status_code=400, detail="unsupported_grant_type")
    client = await _client(db, body.clientId)
    if client is None:
        raise HTTPException(status_code=401, detail="invalid_client")

    async with db.execute("SELECT * FROM oauth_codes WHERE code = ?", (body.code,)) as c:
        row = await c.fetchone()
    if (row is None or row["used"] or row["client_id"] != body.clientId
            or row["redirect_uri"] != body.redirectUri):
        raise HTTPException(status_code=400, detail="invalid_grant")

    exp = datetime.fromisoformat(row["expires_at"])
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="expired_code")

    if row["code_challenge"]:
        if hardened(request):
            if not body.codeVerifier or not _verify_pkce(
                    body.codeVerifier, row["code_challenge"], row["code_challenge_method"]):
                raise HTTPException(status_code=400, detail="invalid_pkce")
        # AUTH-OAUTH-PKCE-001 (default): a code_challenge is present but the
        # code_verifier is never checked - PKCE is silently downgraded.
    elif body.clientSecret != client["client_secret"]:
        raise HTTPException(status_code=401, detail="invalid_client_secret")

    await db.execute("UPDATE oauth_codes SET used = 1 WHERE id = ?", (row["id"],))   # single-use
    await db.commit()

    async with db.execute("SELECT * FROM users WHERE id = ?", (row["user_id"],)) as c:
        u = await c.fetchone()

    access = jwt.encode(
        {"sub": str(u["id"]), "iss": config.JWT_ISSUER, "scope": row["scope"], "exp": _ts(TOKEN_TTL)},
        config.JWT_SECRET, algorithm="HS256",
    )
    id_token = jwt.encode(
        {"sub": str(u["id"]), "iss": config.JWT_ISSUER, "aud": body.clientId,
         "email": u["email"], "name": u["full_name"], "exp": _ts(TOKEN_TTL)},
        PRIVATE_PEM, algorithm="RS256", headers={"kid": KID},
    )
    return {
        "access_token": access, "id_token": id_token,
        "token_type": "Bearer", "expires_in": TOKEN_TTL, "scope": row["scope"],
    }


@router.get("/api/oauth/clients/{client_id}")
async def client_metadata(
    client_id: str,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    # Public client metadata for the consent screen (name + registered redirects).
    # No secret is ever returned.
    client = await _client(db, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="invalid_client")
    return {
        "clientId": client["client_id"],
        "name": client["name"],
        "logoUri": client["logo_uri"],
        "redirectUris": client["redirect_uris"].split(),
    }


@router.get("/api/oauth/userinfo")
async def userinfo(user: dict = Depends(require_auth)):
    return {"sub": str(user["id"]), "email": user["email"], "name": user["full_name"]}


@router.get("/api/oauth/jwks")
async def jwks():
    return JWKS


@router.get("/api/oauth/.well-known/openid-configuration", include_in_schema=False)
async def discovery():
    api = f"http://localhost:{config.PORT}"
    return {
        "issuer":                              config.JWT_ISSUER,
        "authorization_endpoint":              f"{api}/api/oauth/authorize",
        "token_endpoint":                      f"{api}/api/oauth/token",
        "userinfo_endpoint":                   f"{api}/api/oauth/userinfo",
        "jwks_uri":                            f"{api}/api/oauth/jwks",
        "id_token_signing_alg_values_supported": ["RS256"],
        "response_types_supported":            ["code"],
        "grant_types_supported":               ["authorization_code"],
        "code_challenge_methods_supported":    ["S256", "plain"],
        "scopes_supported":                    ["openid", "profile", "email"],
    }
