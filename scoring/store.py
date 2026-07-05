"""
Solve store - a SEPARATE, local record of which vulns have been exploited.

Deliberately isolated from the target:
  - it lives at scoring/data/solves.db (its own SQLite file), NOT vulnforge.db,
  - it is never served over HTTP and never on a path the app can read, so the
    app's own SQL injection / path traversal cannot surface, dump, or corrupt
    the scoreboard.

The app-side detectors (later phases) call record_solve(); the viewer reads via
get_solves(). First solve wins - a re-exploit never overwrites the timestamp.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_DB = Path(__file__).resolve().parent / "data" / "solves.db"


def _conn() -> sqlite3.Connection:
    _DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS solves ("
        "  vuln_id TEXT PRIMARY KEY,"
        "  first_solved_at TEXT NOT NULL,"
        "  evidence TEXT"
        ")"
    )
    return conn


def record_solve(vuln_id: str, evidence: dict | None = None) -> bool:
    """Record the FIRST time a vuln is exploited.

    Idempotent: returns True only when this call newly recorded the solve, and
    False if it was already solved (the original timestamp/evidence are kept).
    """
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with _conn() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO solves (vuln_id, first_solved_at, evidence) VALUES (?, ?, ?)",
            (vuln_id, now, json.dumps(evidence) if evidence else None),
        )
        return cur.rowcount > 0


def get_solves() -> dict:
    """Return {vuln_id: {'first_solved_at': str, 'evidence': dict|None}}."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT vuln_id, first_solved_at, evidence FROM solves"
        ).fetchall()
    return {
        r[0]: {"first_solved_at": r[1], "evidence": json.loads(r[2]) if r[2] else None}
        for r in rows
    }


def reset() -> None:
    """Wipe all solves (for a fresh run or a test)."""
    with _conn() as conn:
        conn.execute("DELETE FROM solves")
