from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import aiosqlite
from ..auth import require_auth
from ..config import config
from ..db import get_db

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class TaskCreate(BaseModel):
    title: str
    body: str | None = None
    priority: str = "medium"


def present(row) -> dict:
    return {
        "id":          row["id"],
        "orgId":       row["org_id"],
        "name":        row["name"],
        "description": row["description"],
        "status":      row["status"],
    }


def present_task(row) -> dict:
    return {
        "id":         row["id"],
        "title":      row["title"],
        "body":       row["body"],
        "status":     row["status"],
        "priority":   row["priority"],
        "assigneeId": row["assignee_id"],
        "dueDate":    row["due_date"],
    }


@router.get("/api/projects")
async def list_projects(
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
    trashed: bool = False,
):
    cond = "deleted_at IS NOT NULL" if trashed else "deleted_at IS NULL"
    async with db.execute(
        f"SELECT * FROM projects WHERE org_id = ? AND {cond} ORDER BY id", (user["org_id"],)
    ) as cur:
        rows = await cur.fetchall()
    return {"projects": [present(r) for r in rows]}


@router.post("/api/projects", status_code=201)
async def create_project(
    body: ProjectCreate,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="name_required")
    cur = await db.execute(
        "INSERT INTO projects (org_id, name, description, status, created_by_id) "
        "VALUES (?, ?, ?, 'active', ?)",
        (user["org_id"], name, body.description, user["id"]),
    )
    project_id = cur.lastrowid
    await db.commit()
    async with db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)) as c:
        row = await c.fetchone()
    return {"project": present(row)}


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None


async def _org_project_row(db, project_id: int, org_id: int):
    async with db.execute(
        "SELECT * FROM projects WHERE id = ? AND org_id = ?", (project_id, org_id)
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")
    return row


@router.patch("/api/projects/{project_id}")
async def update_project(
    project_id: int,
    body: ProjectUpdate,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    await _org_project_row(db, project_id, user["org_id"])
    updates: dict = {}
    if body.name is not None:
        n = body.name.strip()
        if not n:
            raise HTTPException(status_code=400, detail="name_required")
        updates["name"] = n
    if body.description is not None:
        updates["description"] = body.description
    if body.status is not None:
        if body.status not in ("active", "archived"):
            raise HTTPException(status_code=400, detail="invalid_status")
        updates["status"] = body.status
    if updates:
        sets = ", ".join(f"{k} = ?" for k in updates)
        await db.execute(f"UPDATE projects SET {sets} WHERE id = ?", [*updates.values(), project_id])
        await db.commit()
    async with db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)) as c:
        row = await c.fetchone()
    return {"project": present(row)}


@router.post("/api/projects/{project_id}/trash")
async def trash_project(
    project_id: int,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    await _org_project_row(db, project_id, user["org_id"])
    await db.execute(
        "UPDATE projects SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?", (project_id,))
    await db.commit()
    return {"ok": True}


@router.post("/api/projects/{project_id}/restore")
async def restore_project(
    project_id: int,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    await _org_project_row(db, project_id, user["org_id"])
    await db.execute("UPDATE projects SET deleted_at = NULL WHERE id = ?", (project_id,))
    await db.commit()
    return {"ok": True}


@router.delete("/api/projects/{project_id}")
async def delete_project(
    project_id: int,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    await _org_project_row(db, project_id, user["org_id"])
    async with db.execute(
        "SELECT stored_name FROM attachments WHERE project_id = ?", (project_id,)
    ) as cur:
        for r in await cur.fetchall():
            try:
                (config.UPLOAD_DIR / r["stored_name"]).unlink(missing_ok=True)
            except OSError:
                pass
    await db.execute(
        "DELETE FROM comments WHERE task_id IN (SELECT id FROM tasks WHERE project_id = ?)",
        (project_id,),
    )
    await db.execute("DELETE FROM attachments WHERE project_id = ?", (project_id,))
    await db.execute("DELETE FROM tasks WHERE project_id = ?", (project_id,))
    await db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    await db.commit()
    return {"ok": True}


@router.get("/api/projects/{project_id}/tasks")
async def list_project_tasks(
    project_id: int,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT * FROM tasks WHERE project_id = ? AND org_id = ? ORDER BY id",
        (project_id, user["org_id"]),
    ) as cur:
        rows = await cur.fetchall()
    return {"tasks": [present_task(r) for r in rows]}


@router.post("/api/projects/{project_id}/tasks", status_code=201)
async def create_task(
    project_id: int,
    body: TaskCreate,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT id FROM projects WHERE id = ? AND org_id = ?",
        (project_id, user["org_id"]),
    ) as cur:
        if await cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="not_found")

    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="title_required")
    priority = body.priority if body.priority in ("low", "medium", "high") else "medium"

    cur = await db.execute(
        "INSERT INTO tasks (project_id, org_id, title, body, status, priority) "
        "VALUES (?, ?, ?, ?, 'open', ?)",
        (project_id, user["org_id"], title, body.body, priority),
    )
    task_id = cur.lastrowid
    await db.commit()
    async with db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)) as c:
        row = await c.fetchone()
    return {"task": present_task(row)}
