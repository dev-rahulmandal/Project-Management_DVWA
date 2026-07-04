# =============================================================================
# API-SHADOW-001 - Shadow integrations endpoint leaks the SCIM provisioning
# credential (chain link 1 of CHAIN-ATO-001).
# OWASP API5:2023 (BFLA) + API9:2023 (improper inventory) | CWE-200 |
# detector: diver_shadow_endpoint
#
# GET /api/internal/integrations is an UNDOCUMENTED (include_in_schema=False)
# admin/ops endpoint that was never locked down. By default ANY authenticated
# member can read it, and it over-exposes the org's integration config -
# including the SCIM provisioning token AND the privileged service-account user
# id. On its own this is "just" an info leak (Medium); its real value is as the
# DISCOVERY step of the account-takeover chain: the leaked token + service-
# account id feed straight into AUTH-SCIM-001 (externalId -> super-admin).
#
# Two-face: hardened() requires an admin role AND redacts the secret; the default
# (challenge) path leaks it to any member.
# =============================================================================
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
        # SECURE: integration secrets are admin-only and redacted even for admins.
        await require_admin(user=user)
        return {
            "scim": {"enabled": True, "token": "***redacted***", "serviceAccountUserId": None},
            "webhooksConfigured": True,
        }

    # VULN (default): over-exposes the provisioning credential + service account to
    # any org member. This is the chain's discovery primitive.
    return {
        "scim": {
            "enabled": True,
            "token": config.SCIM_TOKEN,             # leaked provisioning credential
            "serviceAccountUserId": 5,              # the privileged service account (super-admin)
            "orgId": config.SCIM_ORG_ID,
        },
        "webhooksConfigured": True,
    }
