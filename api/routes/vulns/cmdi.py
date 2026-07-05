import asyncio
import platform
import subprocess

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ...auth import require_admin
from ...hardening import hardened

router = APIRouter()

_FLAG = "-n" if platform.system() == "Windows" else "-c"


class PingRequest(BaseModel):
    host: str


@router.post("/api/admin/diagnostics/ping")
async def ping(request: Request, body: PingRequest, user: dict = Depends(require_admin)):
    try:
        if hardened(request):
            proc = await asyncio.to_thread(
                subprocess.run,
                ["ping", _FLAG, "1", body.host],
                shell=False, capture_output=True, text=True, timeout=10,
            )
        else:
            proc = await asyncio.to_thread(
                subprocess.run,
                f"ping {_FLAG} 1 {body.host}",
                shell=True, capture_output=True, text=True, timeout=10,
            )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="timeout")
    return {"output": proc.stdout + proc.stderr}
