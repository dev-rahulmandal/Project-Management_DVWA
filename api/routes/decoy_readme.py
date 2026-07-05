import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import require_auth
from ..db import get_db

router = APIRouter()

_DOCS: dict[str, str] = {
    "readme": (
        "# Project README\n\n"
        "This project tracks tasks and collaborators for your organization. "
        "Use the dashboard to create tasks, invite members, and review activity.\n"
    ),
    "changelog": (
        "# Changelog\n\n"
        "## 1.4.0\n- Added task priorities and due dates.\n"
        "## 1.3.0\n- Introduced project trash / restore.\n"
        "## 1.2.0\n- Org-scoped project listing.\n"
    ),
    "license": (
        "MIT License\n\n"
        "Permission is hereby granted, free of charge, to any person obtaining a "
        "copy of this software and associated documentation files, to deal in the "
        "software without restriction.\n"
    ),
}


@router.get("/api/projects/{project_id}/readme")
async def get_project_readme(
    project_id: int,
    doc: str = Query("readme"),
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT id FROM projects WHERE id = ? AND org_id = ?",
        (project_id, user["org_id"]),
    ) as cur:
        if await cur.fetchone() is None:
            raise HTTPException(status_code=404, detail="not_found")

    if doc not in _DOCS:
        raise HTTPException(status_code=400, detail="invalid_doc")

    return {"doc": doc, "content": _DOCS[doc]}
