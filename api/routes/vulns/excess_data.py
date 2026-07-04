# =============================================================================
# API-EXCESSDATA-001 - Excessive Data Exposure (read-side BOPLA).
# OWASP API3:2023 | CWE-200 | detector: diver_excessive_data
#
# GET /api/users/{id} returns the FULL user row - including password_hash,
# internal_notes, and is_super_admin - instead of a safe projection. The lookup
# is org-scoped (404 for other tenants), so this is purely object-PROPERTY-level
# over-exposure, not a cross-tenant (BOLA) flaw. The /api/users list and /api/me
# both project safely; this detail route is the deliberate leak.
#
# Secured twin API-EXCESSDATA-001-SAFE returns only the caller-appropriate
# fields (no hash, no internal notes).
# =============================================================================
from fastapi import APIRouter, Depends, HTTPException, Request
import aiosqlite
from ...auth import require_auth
from ...db import get_db
from ...hardening import hardened

router = APIRouter()


def present_full(row) -> dict:
    # OVER-EXPOSING: leaks password_hash + internal_notes + is_super_admin.
    return {
        "id":            row["id"],
        "email":         row["email"],
        "fullName":      row["full_name"],
        "role":          row["role"],
        "orgId":         row["org_id"],
        "isSuperAdmin":  bool(row["is_super_admin"]),
        "internalNotes": row["internal_notes"],
        "passwordHash":  row["password_hash"],
        "createdAt":     row["created_at"],
    }


def present_safe(row) -> dict:
    return {
        "id":       row["id"],
        "email":    row["email"],
        "fullName": row["full_name"],
        "role":     row["role"],
        "orgId":    row["org_id"],
    }


async def _org_user(db, user_id: int, org_id: int):
    async with db.execute(
        "SELECT * FROM users WHERE id = ? AND org_id = ?", (user_id, org_id)
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")
    return row


# ---- Two-face route: vuln path, behavior chosen at runtime by hardened() -----
@router.get("/api/users/{user_id}")
async def get_user(
    request: Request,
    user_id: int,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    row = await _org_user(db, user_id, user["org_id"])
    if hardened(request):
        return {"user": present_safe(row)}
    else:
        return {"user": present_full(row)}
