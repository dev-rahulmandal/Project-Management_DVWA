"""
Two-face behavior selector for the "kill the tells" build split.

Every catalogued vuln lives at ONE neutrally-named route. Inside the handler,
`hardened(...)` decides whether to take the secure path (True) or the vulnerable
path (False). There is NO -vuln/-SAFE route suffix to enumerate.

Resolution order:
  1. LAB ONLY (config.VF_LAB): a per-request override lets the verify harness
     drive both faces against one running stack without a restart -
       * HTTP:      header  X-VF-Harden: 1 | 0
       * WebSocket: query   ?harden=1 | 0
     The override exists solely for the dev/verification scaffolding and is
     compiled out of a challenge build (VF_LAB=0), so the deployed target has no
     such tell.
  2. Otherwise: config.VF_HARDENED (challenge deploy = 0 = vulnerable by default).

Phase C will additionally gate select vulns on realistic in-app STATE (account,
workflow step, feature-flag row) so the bug only fires mid-flow - layered on top
of this, never replacing the neutral single-route shape.
"""
from __future__ import annotations

from typing import Optional

from starlette.requests import HTTPConnection

from .config import config


def _parse_flag(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    return value.strip() == "1"


def hardened(conn: HTTPConnection | None = None) -> bool:
    """Return True if the secure path should run for this request.

    Pass the Starlette Request (HTTP) or WebSocket - both are HTTPConnection, so
    headers and query params are available uniformly. Pass nothing to read the
    global default only.
    """
    if conn is not None and config.VF_LAB:
        override = _parse_flag(conn.headers.get("X-VF-Harden"))
        if override is None:
            override = _parse_flag(conn.query_params.get("harden"))
        if override is not None:
            return override
    return config.VF_HARDENED
