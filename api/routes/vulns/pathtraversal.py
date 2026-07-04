# =============================================================================
# API-PATHTRAV-001 - Path traversal in attachment download.
# OWASP A01:2021 (Broken Access Control) | CWE-22 | detector: diver_path_traversal
#
# GET /api/attachments?name=... joins the user-supplied name onto a base
# directory with no containment check, so "../api/config.py" (or deeper)
# escapes the directory and reads arbitrary files on the host.
#
# Secured twin API-PATHTRAV-001-SAFE resolves the path and refuses anything that
# does not stay within the base directory.
# =============================================================================
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from ...auth import require_auth
from ...hardening import hardened

router = APIRouter()

# Legit "attachments" live under the project's db/ folder (schema.sql, seed.sql).
_BASE = Path(__file__).resolve().parents[3] / "db"
_MAX = 2000


def _read(target: Path) -> str:
    return target.read_text(encoding="utf-8", errors="replace")[:_MAX]


# ---- Two-face route: hardened() picks secure vs. vulnerable at runtime -------
@router.get("/api/attachments")
async def attachment(request: Request, name: str = Query(...), user: dict = Depends(require_auth)):
    if hardened(request):
        # SECURED (negative control): enforce path stays in _BASE.
        target = (_BASE / name).resolve()
        if not target.is_relative_to(_BASE.resolve()):
            raise HTTPException(status_code=400, detail="invalid_path")
        try:
            return {"name": name, "content": _read(target)}
        except OSError:
            raise HTTPException(status_code=404, detail="not_found")
    else:
        # VULNERABLE (intentional): no containment check.
        target = _BASE / name           # "../api/config.py" escapes _BASE
        try:
            return {"name": name, "content": _read(target)}
        except OSError:
            raise HTTPException(status_code=404, detail="not_found")
