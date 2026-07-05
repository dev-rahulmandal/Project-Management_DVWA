import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Request

from ...auth import require_admin, require_auth
from ...config import config
from ...db import get_db

router = APIRouter()


@router.get("/api/internal/integrations", include_in_schema=False)
async def integrations_config(
    request: Request,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    from ...hardening import hardened

    if hardened(request):
        await require_admin(user=user)
        return {
            "scim": {"enabled": True, "token": "***redacted***", "serviceAccountUserId": None},
            "webhooksConfigured": True,
        }

    return {
        "scim": {
            "enabled": True,
            "token": config.SCIM_TOKEN,
            "serviceAccountUserId": 5,
            "orgId": config.SCIM_ORG_ID,
        },
        "webhooksConfigured": True,
    }
