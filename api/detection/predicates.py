from __future__ import annotations

import base64
import hashlib
import pickletools
import re
from dataclasses import dataclass
from urllib.parse import urlparse

from jose import jwt as _jose_jwt

from .stateful import brute as _brute, dblrefund as _dblrefund, replay as _replay

_CORS_TRUSTED = {"http://localhost:8082"}
_SSRF_MARKER = "ASIA5J7KQP2XR8VNZW3T"
_REDACTED = "***redacted***"
_RESOURCE_MAX = 100


@dataclass
class Ctx:
    user: dict | None
    method: str
    path: str
    query: dict
    req_headers: dict
    origin: str | None
    status: int
    resp_headers: dict
    resp_json: dict | None
    resp_text: str
    hardened: bool
    req_json: dict | None = None


def _token_alg(auth_header: str | None) -> str | None:
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return None
    token = auth_header.split(None, 1)[1].strip()
    try:
        return (_jose_jwt.get_unverified_header(token) or {}).get("alg")
    except Exception:
        return None


def _is_external_redirect(location: str | None) -> bool:
    if not location:
        return False
    if location.startswith("//"):
        return True
    parsed = urlparse(location)
    return bool(parsed.scheme or parsed.netloc)


def _bola(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    u = ctx.user
    if not u or u.get("is_super_admin"):
        return False
    proj = (ctx.resp_json or {}).get("project") or {}
    return "orgId" in proj and proj.get("orgId") != u.get("org_id")


def _bfla(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    u = ctx.user
    if not u or u.get("is_super_admin") or u.get("role") in ("admin", "owner"):
        return False
    return "entries" in (ctx.resp_json or {})


def _excess(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    return "passwordHash" in ((ctx.resp_json or {}).get("user") or {})


def _ssrf(ctx: Ctx) -> bool:
    if ctx.hardened:
        return False
    return _SSRF_MARKER in (ctx.resp_text or "")


def _cors(ctx: Ctx) -> bool:
    if ctx.hardened:
        return False
    origin = ctx.origin
    if not origin or origin in _CORS_TRUSTED:
        return False
    acao = ctx.resp_headers.get("access-control-allow-origin")
    acac = (ctx.resp_headers.get("access-control-allow-credentials") or "").lower()
    return acao == origin and acac == "true"


def _massassign(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    u = ctx.user
    resp = ctx.resp_json or {}
    if not u:
        return False
    if resp.get("isSuperAdmin") is True and not u.get("is_super_admin"):
        return True
    if resp.get("role") in ("owner", "admin") and u.get("role") == "member":
        return True
    if resp.get("orgId") is not None and resp.get("orgId") != u.get("org_id"):
        return True
    return False


def _misconfig(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    secret = (ctx.resp_json or {}).get("jwtSecret")
    return secret is not None and secret != _REDACTED


def _resource(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    try:
        limit = int(ctx.query.get("limit", "50"))
    except (TypeError, ValueError):
        return False
    return limit > _RESOURCE_MAX


def _shadow(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    token = ((ctx.resp_json or {}).get("scim") or {}).get("token")
    return token is not None and token != _REDACTED


def _jwt_none(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    return _token_alg(ctx.req_headers.get("authorization")) == "none"


def _open_redirect(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status != 307:
        return False
    return _is_external_redirect(ctx.resp_headers.get("location"))


def _sqli(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    u = ctx.user
    if not u or u.get("is_super_admin"):
        return False
    results = (ctx.resp_json or {}).get("results")
    if not isinstance(results, list):
        return False
    own = u.get("org_id")
    return any(isinstance(r, dict) and r.get("orgId") not in (None, own) for r in results)


def _pathtrav(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    return ".." in (ctx.query.get("name") or "")


def _biz_expose(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    return "internalId" in ((ctx.resp_json or {}).get("order") or {})


def _scim_escalation(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status not in (200, 201):
        return False
    return (ctx.resp_json or {}).get("linked") is True


def _biz_refund(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    return "creditBalance" in (ctx.resp_json or {})


def _biz_freeorder(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status not in (200, 201):
        return False
    order = (ctx.resp_json or {}).get("order") or {}
    return (order.get("status") == "fulfilled"
            and (order.get("credits") or 0) > 0
            and order.get("amountCents") == 0)


def _biz_coupon(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status not in (200, 201):
        return False
    order = (ctx.resp_json or {}).get("order") or {}
    return (order.get("discountCents") or 0) > 0


def _webhook_sig(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    return "x-vf-signature" not in ctx.req_headers


_SSTI_GADGET = re.compile(
    r"\bcycler\b|\blipsum\b|\bjoiner\b|\bnamespace\b|\battr\s*\(|\|\s*attr\b", re.IGNORECASE)
_SHELL_META = re.compile(r"[;&|`\n]|\$\(")
_PICKLE_EXEC_OPS = {"REDUCE", "INST", "OBJ", "NEWOBJ", "NEWOBJ_EX", "GLOBAL", "STACK_GLOBAL"}


def _pickle_dangerous(raw: bytes) -> bool:
    try:
        for op, _arg, _pos in pickletools.genops(raw):
            if op.name in _PICKLE_EXEC_OPS:
                return True
    except Exception:
        return False
    return False


def _ssti(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    tmpl = (ctx.req_json or {}).get("template")
    return isinstance(tmpl, str) and bool(_SSTI_GADGET.search(tmpl))


def _cmdi(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    host = (ctx.req_json or {}).get("host")
    return isinstance(host, str) and bool(_SHELL_META.search(host))


def _deserial(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    data = (ctx.req_json or {}).get("data")
    if not isinstance(data, str):
        return False
    try:
        raw = base64.b64decode(data)
    except Exception:
        return False
    return _pickle_dangerous(raw)


def _reset(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    rj = ctx.req_json or {}
    email, token = rj.get("email"), rj.get("token")
    if not isinstance(email, str) or not isinstance(token, str):
        return False
    return token == hashlib.md5(email.strip().lower().encode()).hexdigest()


def _oauth_jwk(ctx: Ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    id_token = (ctx.req_json or {}).get("idToken")
    if not isinstance(id_token, str):
        return False
    try:
        header = _jose_jwt.get_unverified_header(id_token) or {}
    except Exception:
        return False
    return bool(header.get("jwk"))


REGISTRY = [
    ("API-BOLA-001",         "GET",   re.compile(r"^/api/projects/\d+$"),              _bola,           True,  False),
    ("API-BFLA-001",         "GET",   re.compile(r"^/api/admin/audit$"),               _bfla,           True,  False),
    ("API-EXCESSDATA-001",   "GET",   re.compile(r"^/api/users/\d+$"),                 _excess,         True,  False),
    ("API-SSRF-001",         "POST",  re.compile(r"^/api/projects/\d+/link-preview$"), _ssrf,           True,  False),
    ("API-CORS-001",         "GET",   re.compile(r"^/api/widget/config$"),             _cors,           False, False),
    ("API-MASSASSIGN-001",   "PATCH", re.compile(r"^/api/me$"),                        _massassign,     True,  False),
    ("API-MISCONFIG-001",    "GET",   re.compile(r"^/api/debug/config$"),              _misconfig,      True,  False),
    ("API-RESOURCE-001",     "GET",   re.compile(r"^/api/events$"),                    _resource,       False, False),
    ("API-SHADOW-001",       "GET",   re.compile(r"^/api/internal/integrations$"),     _shadow,         True,  False),
    ("AUTH-JWT-002",         "GET",   re.compile(r"^/api/v1/profile$"),                _jwt_none,       False, False),
    ("AUTH-REDIRECT-001",    "GET",   re.compile(r"^/api/auth/continue$"),             _open_redirect,  False, False),
    ("AUTH-OAUTH-SSRF-001",  "POST",  re.compile(r"^/api/oauth/register$"),            _ssrf,           True,  False),
    ("WEBHOOK-SSRF-001",     "POST",  re.compile(r"^/api/webhooks/\d+/test$"),         _ssrf,           True,  False),
    ("API-SQLI-001",         "GET",   re.compile(r"^/api/projects/search$"),           _sqli,           True,  False),
    ("API-PATHTRAV-001",     "GET",   re.compile(r"^/api/attachments$"),               _pathtrav,       False, False),
    ("API-BIZ-EXPOSE-001",   "GET",   re.compile(r"^/api/billing/orders/[^/]+$"),      _biz_expose,     True,  False),
    ("AUTH-SCIM-001",        "POST",  re.compile(r"^/api/scim/v2/Users$"),             _scim_escalation,True,  False),
    ("API-BIZ-REFUND-001",   "POST",  re.compile(r"^/api/billing/refund$"),            _biz_refund,     True,  False),
    ("API-BIZ-FREEORDER-001","POST",  re.compile(r"^/api/billing/orders/import$"),     _biz_freeorder,  True,  False),
    ("API-BIZ-COUPON-001",   "POST",  re.compile(r"^/api/billing/orders/quick$"),      _biz_coupon,     True,  False),
    ("WEBHOOK-SIG-001",      "POST",  re.compile(r"^/api/webhooks/inbound/billing$"),  _webhook_sig,    False, False),
    ("API-SSTI-001",         "POST",  re.compile(r"^/api/notifications/preview$"),     _ssti,           False, True),
    ("API-CMDI-001",         "POST",  re.compile(r"^/api/admin/diagnostics/ping$"),    _cmdi,           False, True),
    ("API-DESERIAL-001",     "POST",  re.compile(r"^/api/preferences/import$"),        _deserial,       False, True),
    ("AUTH-RESET-001",       "POST",  re.compile(r"^/api/auth/reset/confirm$"),        _reset,          False, True),
    ("AUTH-OAUTH-JWK-001",   "POST",  re.compile(r"^/api/oauth/verify-id-token$"),     _oauth_jwk,      False, True),
    ("AUTH-BRUTE-001",       "POST",  re.compile(r"^/api/auth/login-attempt$"),        _brute,          False, True),
    ("WEBHOOK-REPLAY-001",   "POST",  re.compile(r"^/api/webhooks/inbound/billing$"),  _replay,         False, True),
    ("API-BIZ-DBLREFUND-001","POST",  re.compile(r"^/api/billing/orders/[^/]+/refund-credit$"), _dblrefund, True, False),
]


def matching(method: str, path: str):
    return [(vid, chk, nr, nq) for (vid, m, rx, chk, nr, nq) in REGISTRY
            if m == method and rx.match(path)]
