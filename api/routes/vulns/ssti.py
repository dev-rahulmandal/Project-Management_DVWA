import jinja2
from jinja2.sandbox import SandboxedEnvironment
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ...auth import require_auth
from ...hardening import hardened

router = APIRouter()

_unsafe_env = jinja2.Environment()
_safe_env = SandboxedEnvironment()

_WAF_BLOCK = ("__", "globals", "popen", "system", "subprocess", "import",
              "builtins", "class", "mro", "subclasses", "getattr")


def _waf_blocked(template: str) -> bool:
    low = template.lower()
    return any(tok in low for tok in _WAF_BLOCK)


class TemplateRequest(BaseModel):
    template: str


def _context(user: dict) -> dict:
    return {"name": user["full_name"], "orgId": user["org_id"]}


@router.post("/api/notifications/preview")
async def preview(request: Request, body: TemplateRequest, user: dict = Depends(require_auth)):
    if hardened(request):
        try:
            rendered = _safe_env.from_string(body.template).render(**_context(user))
        except jinja2.exceptions.SecurityError:
            raise HTTPException(status_code=400, detail="blocked")
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"render_error: {exc}")
        return {"preview": rendered}
    else:
        if _waf_blocked(body.template):
            raise HTTPException(status_code=403, detail="forbidden")
        try:
            rendered = _unsafe_env.from_string(body.template).render(**_context(user))
        except Exception as exc:  # noqa: BLE001 - surface render errors to the caller
            raise HTTPException(status_code=400, detail=f"render_error: {exc}")
        return {"preview": rendered}
