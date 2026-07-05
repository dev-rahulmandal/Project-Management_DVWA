from fastapi import APIRouter, Depends, HTTPException, Request
import aiosqlite
from ...auth import require_auth, require_admin
from ...db import get_db
from ...hardening import hardened

router = APIRouter()


def present_audit(row) -> dict:
    return {
        "id":           row["id"],
        "userId":       row["user_id"],
        "action":       row["action"],
        "resourceType": row["resource_type"],
        "resourceId":   row["resource_id"],
        "createdAt":    row["created_at"],
    }


async def _org_audit(db, org_id: int) -> list[dict]:
    async with db.execute(
        "SELECT * FROM audit_logs WHERE org_id = ? ORDER BY id DESC", (org_id,)
    ) as cur:
        rows = await cur.fetchall()
    return [present_audit(r) for r in rows]


@router.get("/api/admin/audit")
async def get_audit_log(
    request: Request,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request):
        if not user["is_super_admin"] and user["role"] not in ("admin", "owner"):
            raise HTTPException(status_code=403, detail="forbidden")
        return {"entries": await _org_audit(db, user["org_id"])}
    else:
        return {"entries": await _org_audit(db, user["org_id"])}
