import csv
import io

import aiosqlite
from fastapi import APIRouter, Depends
from fastapi.responses import Response

from ..auth import require_auth
from ..db import get_db

router = APIRouter()


@router.get("/api/activity")
async def activity_feed(
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
    action: str | None = None,
    resourceType: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    where = ["a.org_id = ?"]
    params: list = [user["org_id"]]
    if action:
        where.append("a.action = ?"); params.append(action)
    if resourceType:
        where.append("a.resource_type = ?"); params.append(resourceType)
    clause = " AND ".join(where)

    async with db.execute(f"SELECT COUNT(*) FROM audit_logs a WHERE {clause}", params) as c:
        total = (await c.fetchone())[0]
    async with db.execute(
        f"SELECT a.action, a.resource_type, a.resource_id, a.created_at, u.full_name AS actor "
        f"FROM audit_logs a LEFT JOIN users u ON u.id = a.user_id WHERE {clause} "
        f"ORDER BY a.id DESC LIMIT ? OFFSET ?",
        (*params, min(max(limit, 1), 200), max(offset, 0)),
    ) as c:
        rows = await c.fetchall()
    return {
        "total": total,
        "activity": [{
            "action": r["action"], "resourceType": r["resource_type"],
            "resourceId": r["resource_id"], "actor": r["actor"], "at": r["created_at"],
        } for r in rows],
    }


@router.get("/api/export/tasks")
async def export_tasks(
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
    format: str = "csv",
):
    async with db.execute(
        "SELECT t.id, p.name AS project, t.title, t.status, t.priority, t.due_date, "
        "u.full_name AS assignee FROM tasks t JOIN projects p ON p.id = t.project_id "
        "LEFT JOIN users u ON u.id = t.assignee_id "
        "WHERE t.org_id = ? AND t.deleted_at IS NULL ORDER BY t.id", (user["org_id"],)
    ) as c:
        rows = await c.fetchall()

    records = [{
        "id": r["id"], "project": r["project"], "title": r["title"], "status": r["status"],
        "priority": r["priority"], "dueDate": r["due_date"], "assignee": r["assignee"],
    } for r in rows]

    if format == "json":
        import json
        return Response(
            content=json.dumps({"tasks": records}, indent=2), media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="tasks.json"'})

    buf = io.StringIO()
    cols = ["id", "project", "title", "status", "priority", "dueDate", "assignee"]
    w = csv.DictWriter(buf, fieldnames=cols)
    w.writeheader()
    for rec in records:
        w.writerow(rec)
    return Response(
        content=buf.getvalue(), media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="tasks.csv"'})
