"""
Dashboard metrics - org-scoped aggregate counts for the overview page.

Legitimate, correctly-secured product surface (part of the Phase-B haystack):
every query is filtered to the caller's org. Not a catalogued vuln.
"""
from datetime import datetime, timedelta, timezone

import aiosqlite
from fastapi import APIRouter, Depends

from ..auth import require_auth
from ..db import get_db

router = APIRouter()


@router.get("/api/dashboard")
async def dashboard(
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    org = user["org_id"]

    async def scalar(q, *a):
        async with db.execute(q, a) as c:
            r = await c.fetchone()
            return r[0] if r else 0

    proj_total = await scalar(
        "SELECT COUNT(*) FROM projects WHERE org_id = ? AND deleted_at IS NULL", org)
    proj_active = await scalar(
        "SELECT COUNT(*) FROM projects WHERE org_id = ? AND status = 'active' AND deleted_at IS NULL", org)
    proj_archived = await scalar(
        "SELECT COUNT(*) FROM projects WHERE org_id = ? AND status = 'archived' AND deleted_at IS NULL", org)

    by_status: dict[str, int] = {}
    async with db.execute(
        "SELECT status, COUNT(*) FROM tasks WHERE org_id = ? AND deleted_at IS NULL GROUP BY status", (org,)
    ) as c:
        for s, n in await c.fetchall():
            by_status[s] = n
    by_priority: dict[str, int] = {}
    async with db.execute(
        "SELECT priority, COUNT(*) FROM tasks WHERE org_id = ? AND deleted_at IS NULL GROUP BY priority", (org,)
    ) as c:
        for p, n in await c.fetchall():
            by_priority[p] = n

    task_total = sum(by_status.values())
    done = by_status.get("done", 0)
    today = datetime.now(timezone.utc).date()
    overdue = await scalar(
        "SELECT COUNT(*) FROM tasks WHERE org_id = ? AND deleted_at IS NULL AND status != 'done' "
        "AND due_date IS NOT NULL AND due_date < ?", org, today.isoformat())
    due_soon = await scalar(
        "SELECT COUNT(*) FROM tasks WHERE org_id = ? AND deleted_at IS NULL AND status != 'done' "
        "AND due_date BETWEEN ? AND ?", org, today.isoformat(), (today + timedelta(days=7)).isoformat())
    members = await scalar("SELECT COUNT(*) FROM users WHERE org_id = ? AND is_active = 1", org)
    unread = await scalar(
        "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0", user["id"])

    activity = []
    async with db.execute(
        "SELECT substr(created_at, 1, 10) d, COUNT(*) FROM audit_logs WHERE org_id = ? "
        "GROUP BY d ORDER BY d DESC LIMIT 14", (org,)
    ) as c:
        activity = [{"date": d, "count": n} for d, n in await c.fetchall()][::-1]

    recent = []
    async with db.execute(
        "SELECT a.action, a.resource_type, a.resource_id, a.created_at, u.full_name "
        "FROM audit_logs a LEFT JOIN users u ON a.user_id = u.id "
        "WHERE a.org_id = ? ORDER BY a.id DESC LIMIT 8", (org,)
    ) as c:
        recent = [{"action": act, "resourceType": rt, "resourceId": ri, "at": at, "actor": actor}
                  for act, rt, ri, at, actor in await c.fetchall()]

    return {
        "projects": {"total": proj_total, "active": proj_active, "archived": proj_archived},
        "tasks": {
            "total": task_total, "byStatus": by_status, "byPriority": by_priority,
            "overdue": overdue, "dueSoon": due_soon,
            "completionRate": round(done / task_total * 100) if task_total else 0,
        },
        "members": members,
        "unreadNotifications": unread,
        "activityByDay": activity,
        "recentActivity": recent,
    }
