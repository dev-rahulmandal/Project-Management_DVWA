# DECOY (DECOY-BOLA-001) - looks like BOLA/IDOR (single comment fetched by a
# sequential global id, crAPI-style bait) but is correctly secured; not a
# catalogued vuln. The lookup is org-scoped, so a comment belonging to another
# org returns 404 instead of leaking the row. Intentional benign noise.
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
    # Org-scoped read: the comment is only returned when it belongs to the
    # caller's org. A bare sequential id from another tenant matches no row
    # under this WHERE clause, so the response is a 404 - never the foreign row.
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
