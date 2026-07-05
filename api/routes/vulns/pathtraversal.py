from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ...auth import require_auth
from ...hardening import hardened

router = APIRouter()

_BASE = Path(__file__).resolve().parents[3] / "db"
_MAX = 2000


def _read(target: Path) -> str:
    return target.read_text(encoding="utf-8", errors="replace")[:_MAX]


@router.get("/api/attachments")
async def attachment(request: Request, name: str = Query(...), user: dict = Depends(require_auth)):
    if hardened(request):
        target = (_BASE / name).resolve()
        if not target.is_relative_to(_BASE.resolve()):
            raise HTTPException(status_code=400, detail="invalid_path")
        try:
            return {"name": name, "content": _read(target)}
        except OSError:
            raise HTTPException(status_code=404, detail="not_found")
    else:
        target = _BASE / name
        try:
            return {"name": name, "content": _read(target)}
        except OSError:
            raise HTTPException(status_code=404, detail="not_found")
