import re

from fastapi import APIRouter, Depends, HTTPException, Request
import aiosqlite
from ...auth import require_auth
from ...db import get_db
from ...hardening import hardened

router = APIRouter()

_SQLI_WAF = re.compile(r"\bor\b|--|/\*|;|\bunion\s+all\b", re.IGNORECASE)


def present(row) -> dict:
    return {
        "id":          row["id"],
        "orgId":       row["org_id"],
        "name":        row["name"],
        "description": row["description"],
        "status":      row["status"],
    }


@router.get("/api/projects/search")
async def search_projects(
    request: Request,
    q: str,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request):
        async with db.execute(
            "SELECT id, org_id, name, description, status FROM projects "
            "WHERE org_id = ? AND name LIKE ?",
            (user["org_id"], f"%{q}%"),
        ) as cur:
            rows = await cur.fetchall()
        return {"results": [present(r) for r in rows]}

    if _SQLI_WAF.search(q):
        raise HTTPException(status_code=403, detail="forbidden")
    sql = (
        "SELECT id, org_id, name, description, status FROM projects "
        f"WHERE org_id = {user['org_id']} AND name LIKE '%{q}%'"
    )
    async with db.execute(sql) as cur:
        rows = await cur.fetchall()
    return {"results": [present(r) for r in rows]}
