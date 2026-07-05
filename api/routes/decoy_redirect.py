from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/api/links/redirect")
async def safe_redirect(to: str = Query("/")):
    if not to.startswith("/") or to[1:2] in ("/", "\\"):
        raise HTTPException(status_code=400, detail="invalid_target")
    return RedirectResponse(url=to, status_code=307)
