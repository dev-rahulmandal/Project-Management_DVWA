from __future__ import annotations

from typing import Optional

from starlette.requests import HTTPConnection

from .config import config


def _parse_flag(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    return value.strip() == "1"


def hardened(conn: HTTPConnection | None = None) -> bool:
    if conn is not None and config.VF_LAB:
        override = _parse_flag(conn.headers.get("X-VF-Harden"))
        if override is None:
            override = _parse_flag(conn.query_params.get("harden"))
        if override is not None:
            return override
    return config.VF_HARDENED
