import aiosqlite
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt

from ..config import config
from ..hardening import hardened

router = APIRouter()

WS_UNAUTHORIZED = 4401


async def ws_authenticate(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"],
                             issuer=config.JWT_ISSUER)
    except JWTError:
        return None
    uid = payload.get("sub")
    if not isinstance(uid, (str, int)):
        return None
    async with aiosqlite.connect(config.DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM users WHERE id = ?", (int(uid),)) as cur:
            row = await cur.fetchone()
    if row is None or not row["is_active"]:
        return None
    return dict(row)


def task_dict(r) -> dict:
    return {"id": r["id"], "projectId": r["project_id"], "orgId": r["org_id"],
            "title": r["title"], "body": r["body"], "status": r["status"],
            "priority": r["priority"]}


async def fetch_task(task_id: int):
    async with aiosqlite.connect(config.DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)) as cur:
            return await cur.fetchone()


async def fetch_audit_log(org_id: int) -> list[dict]:
    async with aiosqlite.connect(config.DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            "SELECT * FROM audit_logs WHERE org_id = ? ORDER BY id", (org_id,)
        ) as cur:
            rows = await cur.fetchall()
    return [{"id": r["id"], "action": r["action"], "resourceType": r["resource_type"],
             "resourceId": r["resource_id"], "ip": r["ip"]} for r in rows]


@router.websocket("/api/ws/activity")
async def activity(websocket: WebSocket, token: str = Query("")):
    user = await ws_authenticate(token)
    if user is None:
        await websocket.close(code=WS_UNAUTHORIZED)
        return
    secure = hardened(websocket)
    await websocket.accept()
    await websocket.send_json({"type": "connected", "userId": user["id"], "orgId": user["org_id"]})
    try:
        while True:
            msg = await websocket.receive_json()
            action = msg.get("type")
            if action == "fetch_task":
                row = await fetch_task(int(msg.get("taskId", 0)))
                if secure:
                    if row is None or row["org_id"] != user["org_id"]:
                        await websocket.send_json({"type": "error", "detail": "forbidden"})
                    else:
                        await websocket.send_json({"type": "task", "task": task_dict(row)})
                else:
                    if row is None:
                        await websocket.send_json({"type": "error", "detail": "not_found"})
                    else:
                        await websocket.send_json({"type": "task", "task": task_dict(row)})
            elif action == "get_audit_log":
                if secure and user["role"] not in ("admin", "owner") and not user["is_super_admin"]:
                    await websocket.send_json({"type": "error", "detail": "forbidden"})
                else:
                    await websocket.send_json({"type": "audit_log",
                                               "entries": await fetch_audit_log(user["org_id"])})
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
            else:
                await websocket.send_json({"type": "error", "detail": "unknown_action"})
    except WebSocketDisconnect:
        return
