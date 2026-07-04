# =============================================================================
# API-BFLA-001 - Broken Function Level Authorization (org audit log).
# OWASP API5:2023 | CWE-862 (Missing Authorization) | detector: diver_bfla
#
# GET /api/admin/audit returns the organization's audit log - an admin-only
# feature. On the vulnerable face it is gated only by require_auth
# (authentication); the function-level check (require_admin) is missing, so any
# authenticated member can read it. It IS org-scoped, so this is purely a
# function-level authz flaw, not a cross-tenant (BOLA) one.
#
# Two-face: hardened(request) selects the secured twin API-BFLA-001-SAFE on the
# same route, which enforces require_admin (403 for a non-admin member).
# =============================================================================
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


# ---- Two-face route: GET /api/admin/audit -----------------------------------
# hardened(request) → True  : secured twin (API-BFLA-001-SAFE), require_admin.
# hardened(request) → False : VULNERABLE (intentional), BFLA - no admin gate.
@router.get("/api/admin/audit")
async def get_audit_log(
    request: Request,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request):
        # SECURED: enforce require_admin (403 for a non-admin member).
        if not user["is_super_admin"] and user["role"] not in ("admin", "owner"):
            raise HTTPException(status_code=403, detail="forbidden")
        return {"entries": await _org_audit(db, user["org_id"])}
    else:
        # BFLA: no require_admin - any member of the org reads the admin audit log.
        return {"entries": await _org_audit(db, user["org_id"])}
