"""
Project file attachments - upload, list, download, delete.

Secure baseline:
  - storage name is server-generated random (no user-controlled path) -> no
    traversal / overwrite,
  - everything is org-scoped (project + attachment must belong to the caller's
    org) -> no cross-tenant access,
  - downloads are forced as octet-stream with nosniff -> uploaded HTML/SVG can't
    render inline (no stored XSS via files),
  - a size cap is enforced.
Intentional variants (path-traversal download, IDOR, inline-XSS serve,
unrestricted upload) are added later as separate, manifested endpoints.
"""
import secrets
from pathlib import Path

import aiosqlite
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..auth import require_auth
from ..config import config
from ..db import get_db

router = APIRouter()

MAX_BYTES = 10 * 1024 * 1024  # 10 MB


def _present(row) -> dict:
    return {
        "id":           row["id"],
        "filename":     row["filename"],
        "contentType":  row["content_type"],
        "sizeBytes":    row["size_bytes"],
        "uploadedById": row["uploaded_by_id"],
        "createdAt":    row["created_at"],
    }


async def _require_org_project(db, project_id: int, org_id: int) -> None:
    async with db.execute(
        "SELECT id FROM projects WHERE id = ? AND org_id = ?", (project_id, org_id)
    ) as cur:
        if await cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="not_found")


@router.post("/api/projects/{project_id}/attachments", status_code=201)
async def upload_attachment(
    project_id: int,
    file: UploadFile = File(...),
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    await _require_org_project(db, project_id, user["org_id"])
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="empty_file")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="file_too_large")

    # Server-controlled random name keeps the original filename out of the path.
    ext = Path(file.filename or "").suffix[:10]
    stored = secrets.token_hex(16) + ext
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (config.UPLOAD_DIR / stored).write_bytes(data)

    cur = await db.execute(
        "INSERT INTO attachments "
        "(org_id, project_id, uploaded_by_id, filename, stored_name, content_type, size_bytes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user["org_id"], project_id, user["id"],
         (file.filename or "file")[:200], stored, file.content_type, len(data)),
    )
    att_id = cur.lastrowid
    await db.commit()
    async with db.execute("SELECT * FROM attachments WHERE id = ?", (att_id,)) as c:
        row = await c.fetchone()
    return {"attachment": _present(row)}


@router.get("/api/projects/{project_id}/attachments")
async def list_attachments(
    project_id: int,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    await _require_org_project(db, project_id, user["org_id"])
    async with db.execute(
        "SELECT * FROM attachments WHERE project_id = ? AND org_id = ? ORDER BY id DESC",
        (project_id, user["org_id"]),
    ) as cur:
        rows = await cur.fetchall()
    return {"attachments": [_present(r) for r in rows]}


@router.get("/api/attachments/{att_id}/download")
async def download_attachment(
    att_id: int,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT * FROM attachments WHERE id = ? AND org_id = ?", (att_id, user["org_id"])
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")
    path = config.UPLOAD_DIR / row["stored_name"]
    if not path.exists():
        raise HTTPException(status_code=404, detail="file_missing")
    # Forced download, never inline -> uploaded markup cannot execute in a browser.
    return FileResponse(
        path,
        media_type="application/octet-stream",
        filename=row["filename"],
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.delete("/api/attachments/{att_id}")
async def delete_attachment(
    att_id: int,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT * FROM attachments WHERE id = ? AND org_id = ?", (att_id, user["org_id"])
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")
    try:
        (config.UPLOAD_DIR / row["stored_name"]).unlink(missing_ok=True)
    except OSError:
        pass
    await db.execute("DELETE FROM attachments WHERE id = ?", (att_id,))
    await db.commit()
    return {"ok": True}
