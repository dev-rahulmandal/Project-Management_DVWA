# =============================================================================
# API-MASSASSIGN-001 - Mass assignment / BOPLA privilege escalation.
# OWASP API3:2023 (BOPLA) | CWE-915 | tier 1 | detector: diver_mass_assignment
#
# PATCH /api/me updates the caller's own profile, but binds EVERY recognized
# key from the request body straight onto the user row - including the
# security-sensitive columns role, is_super_admin, and org_id. A member can
# promote themselves to owner / super-admin (or hop tenants) by sending those
# fields, even though the UI only ever submits fullName.
#
# Secured twin API-MASSASSIGN-001-SAFE = PATCH /api/secure/me, which binds only
# an allowlist of caller-editable fields ({fullName}); sensitive keys in the
# body are silently ignored, so no escalation occurs.
# =============================================================================
from fastapi import APIRouter, Depends, Request
import aiosqlite
from ...auth import require_auth
from ...db import get_db
from ...hardening import hardened

router = APIRouter()


# Every key here is bound onto the user row by the VULNERABLE handler. The bug
# is the breadth of this map: role / is_super_admin / org_id are server-owned
# and must never be settable by the object's own user.
BINDABLE = {
    "fullName":     "full_name",
    "email":        "email",
    "role":         "role",
    "isSuperAdmin": "is_super_admin",
    "orgId":        "org_id",
}

# The secured twin only honors these - the fields a user legitimately edits.
ALLOWLIST = {
    "fullName": "full_name",
}


def present_user(row) -> dict:
    return {
        "id":           row["id"],
        "email":        row["email"],
        "fullName":     row["full_name"],
        "role":         row["role"],
        "orgId":        row["org_id"],
        "isSuperAdmin": bool(row["is_super_admin"]),
    }


def _build_updates(payload: dict, field_map: dict) -> dict:
    updates = {}
    for key, value in payload.items():
        col = field_map.get(key)
        if col is None:
            continue
        if col == "is_super_admin":
            value = 1 if value else 0
        updates[col] = value
    return updates


async def _apply_and_return(db, user_id: int, updates: dict) -> dict:
    if updates:
        sets = ", ".join(f"{col} = ?" for col in updates)
        params = [*updates.values(), user_id]
        await db.execute(f"UPDATE users SET {sets} WHERE id = ?", params)
        await db.commit()
    async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cur:
        row = await cur.fetchone()
    return present_user(row)


# ---- VULNERABLE (intentional): binds sensitive fields from the body ----------
# Single route; behavior is chosen at runtime by hardened(request). When
# hardened, only an allowlist of caller-editable fields is bound (the secured
# twin API-MASSASSIGN-001-SAFE); otherwise the whole body is trusted (the vuln).
@router.patch("/api/me")
async def update_me(
    request: Request,
    payload: dict,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request):
        # Only caller-editable fields are bound; sensitive keys are ignored.
        updates = _build_updates(payload, ALLOWLIST)
        return await _apply_and_return(db, user["id"], updates)
    else:
        # Mass assignment: the whole body is trusted, including role/is_super_admin/org_id.
        updates = _build_updates(payload, BINDABLE)
        return await _apply_and_return(db, user["id"], updates)
