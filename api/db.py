import aiosqlite
from pathlib import Path
from .config import config

_SCHEMA = Path(__file__).parent.parent / "db" / "schema.sql"
_SEED   = Path(__file__).parent.parent / "db" / "seed.sql"
_BULK   = Path(__file__).parent.parent / "db" / "seed_bulk.sql"


async def init_db() -> None:
    async with aiosqlite.connect(config.DB_PATH) as conn:
        async with conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'users'"
        ) as cur:
            initialized = await cur.fetchone() is not None
        if not initialized:
            await conn.executescript(_SCHEMA.read_text(encoding="utf-8"))
            await conn.executescript(_SEED.read_text(encoding="utf-8"))
            if _BULK.exists():
                await conn.executescript(_BULK.read_text(encoding="utf-8"))
            await conn.commit()
            await _materialize_seed_attachments(conn)


async def _materialize_seed_attachments(conn) -> None:
    try:
        async with conn.execute(
            "SELECT stored_name, filename, size_bytes FROM attachments"
        ) as cur:
            rows = await cur.fetchall()
    except Exception:
        return
    if not rows:
        return
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    for stored_name, filename, size_bytes in rows:
        dest = config.UPLOAD_DIR / stored_name
        if dest.exists():
            continue
        header = f"Prolane sample attachment\nOriginal file: {filename}\n\n".encode("utf-8")
        size = int(size_bytes or 0)
        if size <= 0:
            data = header
        elif size <= len(header):
            data = header[:size]
        else:
            data = header + b"." * (size - len(header))
        try:
            dest.write_bytes(data)
        except OSError:
            pass


async def get_db():
    async with aiosqlite.connect(config.DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys = ON")
        await conn.execute("PRAGMA busy_timeout = 5000")
        yield conn
