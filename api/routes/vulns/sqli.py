# =============================================================================
# API-SQLI-001 - SQL injection in project search (string-built query).
# OWASP A03:2021 (Injection) | CWE-89 | detector: diver_sqli
#
# GET /api/projects/search?q=... builds its WHERE clause by concatenating the
# user-supplied q straight into the SQL string. An attacker breaks out of the
# LIKE literal and neutralizes the org_id filter, reading other tenants' rows
# (and could UNION other tables). Everywhere else in the app uses parameterized
# queries - this endpoint is the deliberate exception.
#
# Secured twin API-SQLI-001-SAFE is the same route under hardened(request): it
# binds q as a parameter, so the same payload is treated as literal search text.
# =============================================================================
import re

from fastapi import APIRouter, Depends, HTTPException, Request
import aiosqlite
from ...auth import require_auth
from ...db import get_db
from ...hardening import hardened

router = APIRouter()

# Phase C - a REAL defense the exploit must DEFEAT. A naive signature WAF blocks
# the canonical `' OR 1=1 --` injection (the first thing a scanner fires), so the
# exploit must pivot to a less-obvious technique (a UNION SELECT that needs no OR
# and no comment). \bor\b matches the OR operator but not the org_id column.
_SQLI_WAF = re.compile(r"\bor\b|--|/\*|;|\bunion\s+all\b", re.IGNORECASE)


def present(row) -> dict:
    return {
        "id":          row["id"],
        "orgId":       row["org_id"],
        "name":        row["name"],
        "description": row["description"],
        "status":      row["status"],
    }


# ---- Single neutral route: behavior chosen at runtime by hardened(request) --
@router.get("/api/projects/search")
async def search_projects(
    request: Request,
    q: str,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request):
        # SECURED (negative control): parameterized - q is bound as a value.
        async with db.execute(
            "SELECT id, org_id, name, description, status FROM projects "
            "WHERE org_id = ? AND name LIKE ?",
            (user["org_id"], f"%{q}%"),
        ) as cur:
            rows = await cur.fetchall()
        return {"results": [present(r) for r in rows]}

    # VULNERABLE (intentional) - but behind a signature WAF. The canonical
    #   q = ' OR '1'='1' --     is blocked (403); the exploit must bypass it, e.g.
    #   q = ' UNION SELECT id,org_id,name,description,status FROM projects WHERE name LIKE '
    # which neutralizes the org_id filter (cross-tenant read) with no OR / comment.
    if _SQLI_WAF.search(q):
        raise HTTPException(status_code=403, detail="blocked_by_filter")
    sql = (
        "SELECT id, org_id, name, description, status FROM projects "
        f"WHERE org_id = {user['org_id']} AND name LIKE '%{q}%'"
    )
    async with db.execute(sql) as cur:
        rows = await cur.fetchall()
    return {"results": [present(r) for r in rows]}
