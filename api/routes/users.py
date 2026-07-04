from fastapi import APIRouter, Depends
import aiosqlite
from ..auth import require_auth
from ..db import get_db

router = APIRouter()


def present_member(row) -> dict:
    return {
        "id":       row["id"],
        "email":    row["email"],
        "fullName": row["full_name"],
        "role":     row["role"],
    }


# Org-scoped team roster: returns ONLY members of the caller's organization.
# Safe projection - password_hash and internal_notes are deliberately excluded.
# An over-exposing variant (BOPLA) or a per-user detail route with an ownership
# flaw (BOLA) would each be a separate, proposed, manifested endpoint - never
# smuggled in under this benign listing.
@router.get("/api/users")
async def list_users(
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT * FROM users WHERE org_id = ? ORDER BY id", (user["org_id"],)
    ) as cur:
        rows = await cur.fetchall()
    return {"users": [present_member(r) for r in rows]}
