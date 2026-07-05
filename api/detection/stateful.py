from __future__ import annotations

import re

_brute_attempts: dict[str, int] = {}
_replay_seen: dict[str, int] = {}
_refund_grants: dict[str, int] = {}

BRUTE_THRESHOLD = 10
_REFUND_PATH = re.compile(r"^/api/billing/orders/([^/]+)/refund-credit$")


def brute(ctx) -> bool:
    if ctx.hardened or ctx.status not in (200, 401):
        return False
    email = (ctx.req_json or {}).get("email")
    if not isinstance(email, str):
        return False
    key = email.strip().lower()
    _brute_attempts[key] = _brute_attempts.get(key, 0) + 1
    return _brute_attempts[key] >= BRUTE_THRESHOLD


def replay(ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    did = (ctx.req_json or {}).get("id")
    if did is None:
        return False
    key = str(did)
    _replay_seen[key] = _replay_seen.get(key, 0) + 1
    return _replay_seen[key] >= 2


def dblrefund(ctx) -> bool:
    if ctx.hardened or ctx.status != 200:
        return False
    granted = (ctx.resp_json or {}).get("granted")
    if isinstance(granted, bool) or not isinstance(granted, (int, float)) or granted <= 0:
        return False
    m = _REFUND_PATH.match(ctx.path)
    if not m:
        return False
    key = m.group(1)
    _refund_grants[key] = _refund_grants.get(key, 0) + 1
    return _refund_grants[key] >= 2


def reset_counters() -> None:
    _brute_attempts.clear()
    _replay_seen.clear()
    _refund_grants.clear()
