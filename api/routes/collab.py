import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_auth
from ..db import get_db

router = APIRouter()


@router.get("/api/notifications")
async def list_notifications(
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
    unreadOnly: bool = False,
    limit: int = 50,
):
    where = "user_id = ?"
    params: list = [user["id"]]
    if unreadOnly:
        where += " AND is_read = 0"
    async with db.execute(
        f"SELECT * FROM notifications WHERE {where} ORDER BY id DESC LIMIT ?",
        (*params, min(max(limit, 1), 200)),
    ) as c:
        rows = await c.fetchall()
    async with db.execute(
        "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0", (user["id"],)
    ) as c:
        unread = (await c.fetchone())[0]
    return {"unreadCount": unread, "notifications": [{
        "id": r["id"], "kind": r["kind"], "title": r["title"], "body": r["body"],
        "link": r["link"], "isRead": bool(r["is_read"]), "createdAt": r["created_at"],
    } for r in rows]}


@router.post("/api/notifications/{nid}/read")
async def mark_read(
    nid: int,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    cur = await db.execute(
        "UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (nid, user["id"]))
    await db.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="not_found")
    return {"ok": True}


@router.post("/api/notifications/read-all")
async def mark_all_read(
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    await db.execute(
        "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0", (user["id"],))
    await db.commit()
    return {"ok": True}


@router.get("/api/members")
async def member_directory(
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT id, full_name, email, role, is_super_admin FROM users "
        "WHERE org_id = ? AND is_active = 1 ORDER BY full_name", (user["org_id"],)
    ) as c:
        rows = await c.fetchall()
    return {"members": [{
        "id": r["id"], "name": r["full_name"], "email": r["email"],
        "role": r["role"], "isSuperAdmin": bool(r["is_super_admin"]),
    } for r in rows]}
