"""
Personal access tokens (scoped API keys) - create, list, revoke - plus PAT-based
authentication and a scope-gated example endpoint (the secure baseline).

A PAT is `vfpat_<random>`; only its SHA-256 hash is stored. require_pat resolves
the bearer to its owner and attaches the token's scopes; endpoints enforce the
exact scope they require. Scope-confusion variants are added as manifested vulns.
"""
import hashlib
import secrets

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from ..auth import require_auth
from ..db import get_db
from ..hardening import hardened

router = APIRouter()
_bearer = HTTPBearer()

ALLOWED_SCOPES = {
    "projects:read", "projects:write",
    "tasks:read", "tasks:write",
    "profile:read",
}


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def require_pat(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    token = credentials.credentials
    if not token.startswith("vfpat_"):
        raise HTTPException(status_code=401, detail="not_a_personal_access_token")
    async with db.execute(
        "SELECT * FROM api_keys WHERE token_hash = ?", (_hash(token),)
    ) as c:
        key = await c.fetchone()
    if key is None:
        raise HTTPException(status_code=401, detail="invalid_key")
    async with db.execute("SELECT * FROM users WHERE id = ?", (key["user_id"],)) as c:
        u = await c.fetchone()
    if u is None or not u["is_active"]:
        raise HTTPException(status_code=401, detail="invalid_key")
    user = dict(u)
    user["scopes"] = (key["scopes"] or "").split()
    return user


# --------------------------- Manage keys -------------------------------------
class KeyCreate(BaseModel):
    name: str
    scopes: list[str]


@router.post("/api/keys", status_code=201)
async def create_key(
    body: KeyCreate,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    # Only allowlisted scopes - a key can never be minted with more than these.
    scopes = [s for s in body.scopes if s in ALLOWED_SCOPES]
    token = "vfpat_" + secrets.token_urlsafe(24)
    cur = await db.execute(
        "INSERT INTO api_keys (user_id, org_id, name, token_hash, prefix, scopes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (user["id"], user["org_id"], body.name.strip() or "key", _hash(token),
         token[:14], " ".join(scopes)),
    )
    await db.commit()
    # Plaintext token returned exactly once.
    return {"id": cur.lastrowid, "name": body.name, "scopes": scopes, "token": token}


@router.get("/api/keys")
async def list_keys(
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT * FROM api_keys WHERE user_id = ? ORDER BY id DESC", (user["id"],)
    ) as cur:
        rows = await cur.fetchall()
    return {"keys": [{
        "id": r["id"], "name": r["name"], "prefix": r["prefix"],
        "scopes": (r["scopes"] or "").split(), "createdAt": r["created_at"],
    } for r in rows]}


@router.delete("/api/keys/{key_id}")
async def revoke_key(
    key_id: int,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    cur = await db.execute(
        "DELETE FROM api_keys WHERE id = ? AND user_id = ?", (key_id, user["id"])
    )
    await db.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="not_found")
    return {"ok": True}


# --------------------- Scope-gated project create ----------------------------
# API-SCOPE-001 - API5:2023 / CWE-863. ONE route; hardened() picks the path.
#   vulnerable: scope checked by PREFIX ("startswith projects") so a read token writes.
#   secure:     requires the EXACT projects:write scope.
class ProjectBody(BaseModel):
    name: str
    description: str | None = None


@router.post("/api/keys/projects", status_code=201)
async def pat_create_project(
    request: Request,
    body: ProjectBody,
    user: dict = Depends(require_pat),
    db: aiosqlite.Connection = Depends(get_db),
):
    scopes = user.get("scopes", [])
    if hardened(request):
        allowed = "projects:write" in scopes
    else:
        allowed = any(s.startswith("projects") for s in scopes)
    if not allowed:
        raise HTTPException(status_code=403, detail="insufficient_scope")
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="name_required")
    cur = await db.execute(
        "INSERT INTO projects (org_id, name, description, status, created_by_id) "
        "VALUES (?, ?, ?, 'active', ?)",
        (user["org_id"], name, body.description, user["id"]),
    )
    await db.commit()
    return {"project": {"id": cur.lastrowid, "name": name}}
