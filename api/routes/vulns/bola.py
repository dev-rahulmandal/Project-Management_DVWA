# =============================================================================
# API-BOLA-001 - Broken Object Level Authorization (cross-tenant IDOR).
# OWASP API1:2023 | CWE-639 | tier 1 | detector: diver_idor_bac
#
# GET /api/projects/{id} authenticates the Bearer token but never checks that
# the project belongs to the caller's org. Sequential ids across orgs (Acme
# 1-3, Globex 4-6) make it trivial: alice (org 1) reads project 4 (Globex).
#
# Secured twin API-BOLA-001-SAFE is the same route under hardened(request),
# which adds the org-ownership check the vuln omits (403 on someone else's
# project). No separate /api/secure surface to enumerate.
# =============================================================================
from fastapi import APIRouter, Depends, HTTPException, Request
import aiosqlite
from ...auth import require_auth
from ...db import get_db
from ...hardening import hardened

router = APIRouter()


def present(row) -> dict:
    return {
        "id":          row["id"],
        "orgId":       row["org_id"],
        "name":        row["name"],
        "description": row["description"],
        "status":      row["status"],
    }


# ---- VULNERABLE (intentional): authenticated, but no ownership check ---------
# Two-face: hardened(request) chooses the secure behavior at runtime; the
# default (else) branch is the BOLA. No separate /api/secure twin route.
@router.get("/api/projects/{project_id}")
async def get_project(
    request: Request,
    project_id: int,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT * FROM projects WHERE id = ?", (project_id,)
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")
    if hardened(request):
        # SECURED (negative control): org-ownership enforced.
        if row["org_id"] != user["org_id"]:
            raise HTTPException(status_code=403, detail="forbidden")
        return {"project": present(row)}
    # BOLA: returns any org's project to any authenticated user.
    return {"project": present(row)}
