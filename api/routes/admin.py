from fastapi import APIRouter, Depends
import aiosqlite
from ..auth import require_admin
from ..db import get_db

router = APIRouter()


@router.get("/api/admin/overview")
async def admin_overview(
    user: dict = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
):
    org_id = user["org_id"]

    async def count(sql: str) -> int:
        async with db.execute(sql, (org_id,)) as cur:
            row = await cur.fetchone()
        return row["c"]

    members = await count("SELECT COUNT(*) AS c FROM users WHERE org_id = ?")
    projects = await count("SELECT COUNT(*) AS c FROM projects WHERE org_id = ?")
    tasks = await count("SELECT COUNT(*) AS c FROM tasks WHERE org_id = ?")

    async with db.execute(
        "SELECT name, plan_tier FROM organizations WHERE id = ?", (org_id,)
    ) as cur:
        org = await cur.fetchone()

    return {
        "org":    {"id": org_id, "name": org["name"], "planTier": org["plan_tier"]},
        "counts": {"members": members, "projects": projects, "tasks": tasks},
    }
