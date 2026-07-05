import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import require_auth
from ..db import get_db

router = APIRouter()

_STATUS = ("open", "in_progress", "done")
_PRIORITY = ("low", "medium", "high")


def present_task(row) -> dict:
    return {
        "id":         row["id"],
        "projectId":  row["project_id"],
        "title":      row["title"],
        "body":       row["body"],
        "status":     row["status"],
        "priority":   row["priority"],
        "assigneeId": row["assignee_id"],
        "dueDate":    row["due_date"],
    }


def present_comment(row) -> dict:
    return {
        "id":         row["id"],
        "body":       row["body"],
        "authorId":   row["author_id"],
        "authorName": row["author_name"],
        "createdAt":  row["created_at"],
    }


async def _org_task(db, task_id: int, org_id: int):
    async with db.execute(
        "SELECT * FROM tasks WHERE id = ? AND org_id = ?", (task_id, org_id)
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")
    return row


@router.get("/api/labels")
async def list_labels(
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT id, name, color FROM labels WHERE org_id = ? ORDER BY name", (user["org_id"],)
    ) as cur:
        rows = await cur.fetchall()
    return {"labels": [{"id": r["id"], "name": r["name"], "color": r["color"]} for r in rows]}


@router.get("/api/tasks")
async def list_tasks(
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
    status: str | None = None,
    priority: str | None = None,
    assigneeId: int | None = None,
    projectId: int | None = None,
    labelId: int | None = None,
    q: str | None = None,
    limit: int = 500,
    offset: int = 0,
):
    where = ["t.org_id = ?", "t.deleted_at IS NULL"]
    params: list = [user["org_id"]]
    if status in _STATUS:
        where.append("t.status = ?"); params.append(status)
    if priority in _PRIORITY:
        where.append("t.priority = ?"); params.append(priority)
    if assigneeId is not None:
        where.append("t.assignee_id = ?"); params.append(assigneeId)
    if projectId is not None:
        where.append("t.project_id = ?"); params.append(projectId)
    if q:
        where.append("(t.title LIKE ? OR t.body LIKE ?)"); params += [f"%{q}%", f"%{q}%"]
    if labelId is not None:
        where.append("t.id IN (SELECT task_id FROM task_labels WHERE label_id = ?)"); params.append(labelId)

    sql = (
        "SELECT t.*, p.name AS project_name, u.full_name AS assignee_name "
        "FROM tasks t JOIN projects p ON p.id = t.project_id "
        "LEFT JOIN users u ON u.id = t.assignee_id "
        f"WHERE {' AND '.join(where)} ORDER BY t.id DESC LIMIT ? OFFSET ?"
    )
    params += [min(max(limit, 1), 1000), max(offset, 0)]
    async with db.execute(sql, params) as cur:
        rows = await cur.fetchall()

    ids = [r["id"] for r in rows]
    labels_by_task: dict[int, list] = {}
    if ids:
        ph = ",".join("?" * len(ids))
        async with db.execute(
            f"SELECT tl.task_id AS tid, l.id AS lid, l.name AS lname, l.color AS lcolor "
            f"FROM task_labels tl JOIN labels l ON l.id = tl.label_id WHERE tl.task_id IN ({ph})", ids
        ) as cur:
            for r in await cur.fetchall():
                labels_by_task.setdefault(r["tid"], []).append(
                    {"id": r["lid"], "name": r["lname"], "color": r["lcolor"]})

    return {"tasks": [{
        "id": r["id"], "projectId": r["project_id"], "projectName": r["project_name"],
        "title": r["title"], "status": r["status"], "priority": r["priority"],
        "assigneeId": r["assignee_id"], "assigneeName": r["assignee_name"],
        "dueDate": r["due_date"], "labels": labels_by_task.get(r["id"], []),
    } for r in rows]}


@router.get("/api/tasks/{task_id}")
async def get_task(
    task_id: int,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    return {"task": present_task(await _org_task(db, task_id, user["org_id"]))}


@router.get("/api/tasks/{task_id}/history")
async def task_history(
    task_id: int,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    await _org_task(db, task_id, user["org_id"])
    async with db.execute(
        "SELECT a.action, a.created_at, u.full_name AS actor FROM audit_logs a "
        "LEFT JOIN users u ON u.id = a.user_id "
        "WHERE a.org_id = ? AND a.resource_type = 'task' AND a.resource_id = ? "
        "ORDER BY a.id DESC LIMIT 50", (user["org_id"], task_id)
    ) as cur:
        rows = await cur.fetchall()
    return {"history": [{"action": r["action"], "at": r["created_at"], "actor": r["actor"]} for r in rows]}


class TaskUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    status: str | None = None
    priority: str | None = None
    assigneeId: int | None = None
    dueDate: str | None = None


@router.patch("/api/tasks/{task_id}")
async def update_task(
    task_id: int,
    body: TaskUpdate,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    await _org_task(db, task_id, user["org_id"])

    updates: dict = {}
    if body.title is not None:
        t = body.title.strip()
        if not t:
            raise HTTPException(status_code=400, detail="title_required")
        updates["title"] = t
    if body.body is not None:
        updates["body"] = body.body
    if body.status is not None:
        if body.status not in _STATUS:
            raise HTTPException(status_code=400, detail="invalid_status")
        updates["status"] = body.status
    if body.priority is not None:
        if body.priority not in _PRIORITY:
            raise HTTPException(status_code=400, detail="invalid_priority")
        updates["priority"] = body.priority
    if body.assigneeId is not None:
        async with db.execute(
            "SELECT 1 FROM users WHERE id = ? AND org_id = ?", (body.assigneeId, user["org_id"])
        ) as cur:
            if await cur.fetchone() is None:
                raise HTTPException(status_code=400, detail="invalid_assignee")
        updates["assignee_id"] = body.assigneeId
    if body.dueDate is not None:
        updates["due_date"] = body.dueDate or None

    if updates:
        sets = ", ".join(f"{k} = ?" for k in updates)
        await db.execute(f"UPDATE tasks SET {sets} WHERE id = ?", [*updates.values(), task_id])
        await db.commit()

    return {"task": present_task(await _org_task(db, task_id, user["org_id"]))}


class CommentCreate(BaseModel):
    body: str


@router.get("/api/tasks/{task_id}/comments")
async def list_comments(
    task_id: int,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    await _org_task(db, task_id, user["org_id"])
    async with db.execute(
        "SELECT c.*, u.full_name AS author_name FROM comments c "
        "JOIN users u ON u.id = c.author_id "
        "WHERE c.task_id = ? AND c.org_id = ? ORDER BY c.id",
        (task_id, user["org_id"]),
    ) as cur:
        rows = await cur.fetchall()
    return {"comments": [present_comment(r) for r in rows]}


@router.post("/api/tasks/{task_id}/comments", status_code=201)
async def add_comment(
    task_id: int,
    body: CommentCreate,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    await _org_task(db, task_id, user["org_id"])
    text = body.body.strip()
    if not text:
        raise HTTPException(status_code=400, detail="empty_comment")
    cur = await db.execute(
        "INSERT INTO comments (task_id, org_id, author_id, body) VALUES (?, ?, ?, ?)",
        (task_id, user["org_id"], user["id"], text),
    )
    cid = cur.lastrowid
    await db.commit()
    async with db.execute(
        "SELECT c.*, u.full_name AS author_name FROM comments c "
        "JOIN users u ON u.id = c.author_id WHERE c.id = ?", (cid,)
    ) as c:
        row = await c.fetchone()
    return {"comment": present_comment(row)}
