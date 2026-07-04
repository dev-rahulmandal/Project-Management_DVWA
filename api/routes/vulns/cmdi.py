# =============================================================================
# API-CMDI-001 - OS command injection in the diagnostics ping tool.
# OWASP A03:2021 (Injection) | CWE-78 | detector: diver_command_injection
#
# POST /api/admin/diagnostics/ping builds a shell command by interpolating the
# user-supplied host into a string run with shell=True. A host like
#   127.0.0.1 & echo PWNED
# chains an arbitrary command. (Admin-gated, but app-admin != OS shell access.)
#
# Secured twin API-CMDI-001-SAFE runs the same ping with shell=False and the
# host passed as a single argv element, so metacharacters are inert.
# =============================================================================
import asyncio
import platform
import subprocess

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ...auth import require_admin
from ...hardening import hardened

router = APIRouter()

# Windows uses -n for count; POSIX uses -c.
_FLAG = "-n" if platform.system() == "Windows" else "-c"


class PingRequest(BaseModel):
    host: str


# ---- TWO-FACE: one neutral route; hardened(request) picks the behavior -------
@router.post("/api/admin/diagnostics/ping")
async def ping(request: Request, body: PingRequest, user: dict = Depends(require_admin)):
    try:
        if hardened(request):
            # SECURED (negative control): no shell, host is one argv element.
            proc = await asyncio.to_thread(
                subprocess.run,
                ["ping", _FLAG, "1", body.host],   # host can't break out of argv
                shell=False, capture_output=True, text=True, timeout=10,
            )
        else:
            # VULNERABLE (intentional): host interpolated into a shell string.
            proc = await asyncio.to_thread(
                subprocess.run,
                f"ping {_FLAG} 1 {body.host}",   # shell injection point
                shell=True, capture_output=True, text=True, timeout=10,
            )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="timeout")
    return {"output": proc.stdout + proc.stderr}
