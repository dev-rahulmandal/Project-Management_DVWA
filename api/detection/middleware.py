from __future__ import annotations

import json

from starlette.requests import Request
from starlette.responses import Response

from ..config import config
from ..hardening import hardened
from .predicates import Ctx, matching

try:
    from scoring.store import record_solve
except Exception:
    record_solve = None

_BUNDLE_SECRET = "sk_live_51Qk7bR2eZvKYlo6C9x3fH8pM4nT0aWqDvXsL"


def _evaluate(preds, request: Request, response, resp_json, resp_text, req_json) -> None:
    try:
        ctx = Ctx(
            user=getattr(request.state, "user", None),
            method=request.method,
            path=request.url.path,
            query=dict(request.query_params),
            req_headers={k.lower(): v for k, v in request.headers.items()},
            origin=request.headers.get("origin"),
            status=response.status_code,
            resp_headers={k.lower(): v for k, v in response.headers.items()},
            resp_json=resp_json,
            resp_text=resp_text,
            hardened=hardened(request),
            req_json=req_json,
        )
        for vuln_id, check, _nr, _nq in preds:
            try:
                if check(ctx):
                    record_solve(vuln_id, {"method": request.method, "path": request.url.path})
            except Exception:
                pass
    except Exception:
        pass


async def detection_middleware(request: Request, call_next):
    if not config.VF_SCORING or record_solve is None:
        return await call_next(request)

    if (_BUNDLE_SECRET in request.headers.get("authorization", "")
            or _BUNDLE_SECRET in request.url.query):
        try:
            record_solve("WEB-SECRET-001", {"surface": "bundle-key-used"})
        except Exception:
            pass

    preds = matching(request.method, request.url.path)
    if not preds:
        return await call_next(request)

    need_resp = any(nr for (_v, _c, nr, _nq) in preds)
    need_req = any(nq for (_v, _c, _nr, nq) in preds)

    req_json = None
    if need_req:
        raw = await request.body()

        async def _replay(_raw=raw):
            return {"type": "http.request", "body": _raw, "more_body": False}

        request._receive = _replay
        try:
            parsed = json.loads(raw.decode("utf-8", "replace")) if raw else None
        except ValueError:
            parsed = None
        req_json = parsed if isinstance(parsed, dict) else None

    response = await call_next(request)

    if not need_resp:
        _evaluate(preds, request, response, resp_json=None, resp_text="", req_json=req_json)
        return response

    body = b""
    async for chunk in response.body_iterator:
        body += chunk
    text = body.decode("utf-8", "replace")
    try:
        parsed = json.loads(text)
    except ValueError:
        parsed = None
    _evaluate(preds, request, response,
              resp_json=parsed if isinstance(parsed, dict) else None,
              resp_text=text, req_json=req_json)

    return Response(
        content=body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
    )
