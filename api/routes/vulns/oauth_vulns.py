import secrets
from urllib.parse import urlparse

import aiosqlite
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from jose import jwt
from pydantic import BaseModel

from ...db import get_db
from ...hardening import hardened
from ...oauth_keys import PUBLIC_PEM
from .ssrf import _host_is_blocked

router = APIRouter()


class ClientRegistration(BaseModel):
    clientName: str
    redirectUris: list[str]
    logoUri: str | None = None


async def _register(db, body: ClientRegistration) -> dict:
    client_id = "dcr_" + secrets.token_urlsafe(8)
    client_secret = secrets.token_urlsafe(24)
    await db.execute(
        "INSERT INTO oauth_clients (client_id, client_secret, name, redirect_uris, logo_uri) "
        "VALUES (?, ?, ?, ?, ?)",
        (client_id, client_secret, body.clientName, " ".join(body.redirectUris), body.logoUri),
    )
    await db.commit()
    return {"clientId": client_id, "clientSecret": client_secret}


async def _fetch_logo(url: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as cl:
            r = await cl.get(url)
        return {"status": r.status_code, "contentType": r.headers.get("content-type"), "body": r.text[:1000]}
    except httpx.HTTPError as exc:
        return {"error": str(exc)}


@router.post("/api/oauth/register", status_code=201)
async def register_client(
    request: Request,
    body: ClientRegistration,
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request) and body.logoUri:
        parsed = urlparse(body.logoUri)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise HTTPException(status_code=400, detail="invalid_logo_uri")
        if _host_is_blocked(parsed.hostname):
            raise HTTPException(status_code=400, detail="blocked_logo_uri")
    reg = await _register(db, body)
    if body.logoUri:
        reg["logoFetch"] = await _fetch_logo(body.logoUri)
    return reg


class VerifyIdToken(BaseModel):
    idToken: str


@router.post("/api/oauth/verify-id-token")
async def verify_id_token(request: Request, body: VerifyIdToken):
    try:
        if hardened(request):
            claims = jwt.decode(body.idToken, PUBLIC_PEM, algorithms=["RS256"],
                                options={"verify_aud": False})
        else:
            header = jwt.get_unverified_header(body.idToken)
            key = header["jwk"] if header.get("jwk") else PUBLIC_PEM
            claims = jwt.decode(body.idToken, key, algorithms=["RS256"],
                                options={"verify_aud": False})
    except Exception:
        raise HTTPException(status_code=401, detail="invalid_token")
    return {"verified": True, "claims": claims}
