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
        if row["org_id"] != user["org_id"]:
            raise HTTPException(status_code=403, detail="forbidden")
        return {"project": present(row)}
    return {"project": present(row)}
