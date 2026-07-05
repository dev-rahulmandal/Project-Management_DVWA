from fastapi import APIRouter, Depends, Request
import aiosqlite
from ...auth import require_auth
from ...db import get_db
from ...hardening import hardened

router = APIRouter()


BINDABLE = {
    "fullName":     "full_name",
    "email":        "email",
    "role":         "role",
    "isSuperAdmin": "is_super_admin",
    "orgId":        "org_id",
}

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


@router.patch("/api/me")
async def update_me(
    request: Request,
    payload: dict,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request):
        updates = _build_updates(payload, ALLOWLIST)
        return await _apply_and_return(db, user["id"], updates)
    else:
        updates = _build_updates(payload, BINDABLE)
        return await _apply_and_return(db, user["id"], updates)
