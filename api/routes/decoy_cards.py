import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_auth
from ..db import get_db

router = APIRouter()


@router.get("/api/comments/{comment_id}")
async def get_comment(
    comment_id: int,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT id, body, task_id, author_id "
        "FROM comments WHERE id = ? AND org_id = ?",
        (comment_id, user["org_id"]),
    ) as cur:
        row = await cur.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="comment_not_found")

    return {
        "comment": {
            "id": row["id"],
            "body": row["body"],
            "taskId": row["task_id"],
            "authorId": row["author_id"],
        }
    }
