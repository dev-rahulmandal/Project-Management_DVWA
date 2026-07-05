import aiosqlite
from fastapi import APIRouter, Depends, Query

from ..auth import require_auth
from ..db import get_db

router = APIRouter()


@router.get("/api/directory/search")
async def directory_search(
    q: str = Query("", max_length=100),
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    like = f"%{q}%"
    async with db.execute(
        "SELECT id, full_name, email FROM users "
        "WHERE org_id = ? AND (full_name LIKE ? OR email LIKE ?) "
        "ORDER BY full_name LIMIT 25",
        (user["org_id"], like, like),
    ) as cur:
        rows = await cur.fetchall()
    return {"results": [{"id": r["id"], "name": r["full_name"], "email": r["email"]} for r in rows]}
