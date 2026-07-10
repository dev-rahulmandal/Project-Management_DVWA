import secrets

import aiosqlite
import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from pydantic import BaseModel

from ..config import config
from ..db import get_db
from ..hardening import hardened

router = APIRouter()
_bearer = HTTPBearer()

USER_SCHEMA = "urn:ietf:params:scim:schemas:core:2.0:User"
LIST_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:ListResponse"
ERROR_SCHEMA = "urn:ietf:params:scim:api:messages:2.0:Error"


def require_scim_token(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
) -> int:
    try:
        ok = secrets.compare_digest(credentials.credentials, config.SCIM_TOKEN)
    except TypeError:
        ok = False  # non-ASCII token bytes: reject cleanly, do not crash
    if not ok:
        raise HTTPException(status_code=401, detail="invalid_provisioning_token")
    return config.SCIM_ORG_ID


def _resource(u: dict) -> dict:
    return {
        "schemas": [USER_SCHEMA],
        "id": str(u["id"]),
        "externalId": u.get("external_id"),
        "userName": u["email"],
        "name": {"formatted": u["full_name"]},
        "active": bool(u.get("is_active", 1)),
        "meta": {"resourceType": "User"},
    }


class ScimName(BaseModel):
    formatted: str | None = None


class ScimUser(BaseModel):
    userName: str
    externalId: str | None = None
    name: ScimName | None = None
    active: bool = True


def _jwt_for(user_id: int) -> str:
    return jwt.encode({"sub": str(user_id), "iss": config.JWT_ISSUER},
                      config.JWT_SECRET, algorithm="HS256")


@router.get("/api/scim/v2/Users")
async def scim_list(
    org_id: int = Depends(require_scim_token),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT * FROM users WHERE org_id = ? ORDER BY id", (org_id,)
    ) as cur:
        rows = await cur.fetchall()
    resources = [_resource(dict(r)) for r in rows]
    return {"schemas": [LIST_SCHEMA], "totalResults": len(resources),
            "startIndex": 1, "itemsPerPage": len(resources), "Resources": resources}


@router.get("/api/scim/v2/Users/{user_id}")
async def scim_get(
    user_id: int,
    org_id: int = Depends(require_scim_token),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT * FROM users WHERE id = ? AND org_id = ?", (user_id, org_id)
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")
    return _resource(dict(row))


@router.post("/api/scim/v2/Users", status_code=201)
async def scim_create(
    request: Request,
    body: ScimUser,
    org_id: int = Depends(require_scim_token),
    db: aiosqlite.Connection = Depends(get_db),
):
    if not hardened(request):
        external = (body.externalId or "").strip()
        if external.isdigit():
            target_id = int(external)
            async with db.execute("SELECT * FROM users WHERE id = ?", (target_id,)) as c:
                existing = await c.fetchone()
            if existing is not None:
                return {**_resource(dict(existing)), "linked": True,
                        "access_token": _jwt_for(target_id)}
        full_name = (body.name.formatted if body.name else None) or body.userName
        pw = bcrypt.hashpw(secrets.token_urlsafe(24).encode(), bcrypt.gensalt(rounds=12)).decode()
        forced_id = int(external) if external.isdigit() else None
        try:
            if forced_id is not None:
                cur = await db.execute(
                    "INSERT INTO users (id, org_id, email, full_name, role, is_super_admin, "
                    "is_active, password_hash, external_id) "
                    "VALUES (?, ?, ?, ?, 'member', 0, 1, ?, ?)",
                    (forced_id, org_id, body.userName, full_name, pw, external),
                )
            else:
                cur = await db.execute(
                    "INSERT INTO users (org_id, email, full_name, role, is_super_admin, "
                    "is_active, password_hash, external_id) "
                    "VALUES (?, ?, ?, 'member', 0, 1, ?, ?)",
                    (org_id, body.userName, full_name, pw, external),
                )
        except aiosqlite.IntegrityError:
            raise HTTPException(status_code=409, detail="user_already_exists")
        await db.commit()
        new_id = cur.lastrowid
        async with db.execute("SELECT * FROM users WHERE id = ?", (new_id,)) as c:
            row = await c.fetchone()
        return {**_resource(dict(row)), "linked": False, "access_token": _jwt_for(new_id)}

    full_name = (body.name.formatted if body.name else None) or body.userName
    pw = bcrypt.hashpw(secrets.token_urlsafe(24).encode(), bcrypt.gensalt(rounds=12)).decode()
    try:
        cur = await db.execute(
            "INSERT INTO users (org_id, email, full_name, role, is_super_admin, "
            "is_active, password_hash, external_id) "
            "VALUES (?, ?, ?, 'member', 0, ?, ?, ?)",
            (org_id, body.userName, full_name, 1 if body.active else 0, pw,
             body.externalId),
        )
    except aiosqlite.IntegrityError:
        raise HTTPException(status_code=409, detail="user_already_exists")
    await db.commit()
    new_id = cur.lastrowid
    async with db.execute("SELECT * FROM users WHERE id = ?", (new_id,)) as c:
        row = await c.fetchone()
    return {**_resource(dict(row)), "access_token": _jwt_for(new_id)}
