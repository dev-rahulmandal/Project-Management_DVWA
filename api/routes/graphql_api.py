import aiosqlite
import strawberry
from fastapi import Depends, Request
from strawberry.fastapi import GraphQLRouter

from ..auth import require_auth
from ..db import get_db
from ..hardening import hardened


@strawberry.type
class User:
    id: int
    email: str
    fullName: str
    role: str
    orgId: int
    internalNotes: str | None = None
    passwordHash: str | None = None


@strawberry.type
class Task:
    id: int
    title: str
    status: str
    priority: str
    orgId: int


def _to_user(row, *, sensitive: bool) -> User:
    return User(
        id=row["id"],
        email=row["email"],
        fullName=row["full_name"],
        role=row["role"],
        orgId=row["org_id"],
        internalNotes=row["internal_notes"] if sensitive else None,
        passwordHash=row["password_hash"] if sensitive else None,
    )


@strawberry.type
class Query:
    @strawberry.field
    async def me(self, info: strawberry.Info) -> User:
        return _to_user(info.context["user"], sensitive=True)

    @strawberry.field
    async def user(self, info: strawberry.Info, id: int) -> User | None:
        db = info.context["db"]
        caller = info.context["user"]
        if hardened(info.context["request"]):
            async with db.execute(
                "SELECT * FROM users WHERE id = ? AND org_id = ?", (id, caller["org_id"])
            ) as cur:
                row = await cur.fetchone()
            return _to_user(row, sensitive=False) if row else None
        async with db.execute("SELECT * FROM users WHERE id = ?", (id,)) as cur:
            row = await cur.fetchone()
        return _to_user(row, sensitive=True) if row else None

    @strawberry.field
    async def tasks(self, info: strawberry.Info) -> list[Task]:
        db = info.context["db"]
        caller = info.context["user"]
        async with db.execute(
            "SELECT * FROM tasks WHERE org_id = ? AND deleted_at IS NULL ORDER BY id",
            (caller["org_id"],),
        ) as cur:
            rows = await cur.fetchall()
        return [
            Task(id=r["id"], title=r["title"], status=r["status"],
                 priority=r["priority"], orgId=r["org_id"])
            for r in rows
        ]


schema = strawberry.Schema(query=Query)


async def _get_context(
    request: Request,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
) -> dict:
    return {"request": request, "user": user, "db": db}


router = GraphQLRouter(schema, path="/graphql", context_getter=_get_context, include_in_schema=False)
