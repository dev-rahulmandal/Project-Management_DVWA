from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...hardening import hardened

router = APIRouter()

_ALLOWED = {"http://localhost:8082"}


def _payload() -> dict:
    return {"orgName": "Northwind Systems", "seats": 25, "plan": "pro"}


@router.get("/api/widget/config")
async def widget_config(request: Request):
    origin = request.headers.get("origin", "")
    resp = JSONResponse(_payload())
    if hardened(request):
        if origin in _ALLOWED:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
    else:
        if origin:
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Access-Control-Allow-Credentials"] = "true"
    return resp
