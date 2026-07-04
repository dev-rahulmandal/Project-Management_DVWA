# DECOY (DECOY-MASSASSIGN-001) - looks like mass assignment but is correctly secured; not a catalogued vuln.
#
# Bait: PATCH /api/me/preferences accepts an arbitrary JSON object of "preferences".
# A scanner/agent will try to smuggle privilege fields (role, isSuperAdmin, orgId,
# is_super_admin, ...) hoping they get blindly written/reflected.
# Reality: the body is read as a plain dict and ONLY an allowlist of presentation
# keys is honored. Everything else is dropped on the floor - never written, never
# echoed. No DB columns back these prefs, so there is nothing to over-write.

from fastapi import APIRouter, Depends, Request

from ..auth import require_auth

router = APIRouter()

# The ONLY keys this endpoint will ever read from the request body. Anything
# else (privilege/identity fields included) is ignored entirely.
_ALLOWED_PREF_KEYS = ("theme", "language", "timezone")


@router.patch("/api/me/preferences")
async def update_preferences(
    request: Request,
    user: dict = Depends(require_auth),
):
    # Bind the body as an untyped dict so unknown keys are simply ignored rather
    # than bound to any model/object. We never iterate the caller-supplied keys -
    # we pull from our own fixed allowlist, so injected keys cannot ride along.
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}

    # Allowlist read: only keys that are BOTH in our allowlist AND were actually
    # provided make it into the response. Privilege fields can never appear here.
    accepted = {key: body[key] for key in _ALLOWED_PREF_KEYS if key in body}

    # Deliberately no DB write: there are no preference columns to mass-assign.
    # We just echo back the sanitized, allowlisted subset.
    return {"preferences": accepted}
