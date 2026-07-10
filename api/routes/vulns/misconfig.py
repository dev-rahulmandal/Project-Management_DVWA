import os
import sys

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ...auth import get_current_user, require_admin
from ...config import config
from ...db import get_db
from ...hardening import hardened

router = APIRouter()

_optional_bearer = HTTPBearer(auto_error=False)


@router.get("/api/debug/config", include_in_schema=False)
async def debug_config(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(_optional_bearer),
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request):
        if credentials is None:
            raise HTTPException(status_code=401, detail="not_authenticated")
        user = await get_current_user(request, credentials=credentials, db=db)
        user = await require_admin(user=user)
        return {
            "jwtIssuer": config.JWT_ISSUER,
            "webOrigin": config.WEB_ORIGIN,
            "jwtSecret": "***redacted***",
        }
    return {
        "jwtSecret":     config.JWT_SECRET,
        "jwtIssuer":     config.JWT_ISSUER,
        "dbPath":        str(config.DB_PATH),
        "webOrigin":     config.WEB_ORIGIN,
        "pythonVersion": sys.version.split()[0],
        "env": {
            k: v for k, v in os.environ.items()
            if k.startswith(("JWT_", "DATABASE_", "SESSION_"))
        },
    }
