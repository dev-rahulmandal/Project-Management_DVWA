#!/usr/bin/env python3
"""
Challenge-readiness check - proves the CHALLENGE face leaks no answer-key signal.

The same codebase has two faces (the lab/challenge build split):
  * LAB       (VF_LAB=1, the default): the verify pipeline's fixture. The per-
                request override header X-VF-Harden:1 flips any vuln to its secure
                twin so the control tests can prove "the secure version holds".
  * CHALLENGE (VF_LAB=0): the deployed hard target. Vulns fire by default and the
                override is IGNORED, so a tester cannot use it to discover which
                behaviour is "the patched one". /api/secure/* routes don't exist
                and shadow endpoints are absent from the OpenAPI.

This script boots the api with VF_LAB=0 + VF_HARDENED=0 and asserts there is no
signal. Run:  python tools/challenge_check.py
"""
import subprocess
import sys
import time
from pathlib import Path

import httpx
from jose import jwt

ROOT = Path(__file__).resolve().parents[1]
PORT = 8091
ORIGIN = f"http://localhost:{PORT}"
DB = "vulnforge_challenge_check.db"


def _forge(sub: int) -> dict:
    tok = jwt.encode({"sub": str(sub), "iss": "vulnforge-api"}, "changeme", algorithm="HS256")
    return {"Authorization": f"Bearer {tok}"}


def main() -> int:
    for s in ("", "-wal", "-shm"):
        (ROOT / f"{DB}{s}").unlink(missing_ok=True)
    env = {
        "JWT_SECRET": "changeme", "JWT_ISSUER": "vulnforge-api",
        "DATABASE_PATH": DB, "API_PORT": str(PORT),
        "VF_HARDENED": "0", "VF_LAB": "0",          # <-- the CHALLENGE face
    }
    import os
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--port", str(PORT)],
        cwd=ROOT, env={**os.environ, **env},
    )
    failures: list[str] = []
    try:
        for _ in range(40):
            try:
                if httpx.get(f"{ORIGIN}/health", timeout=2).status_code < 500:
                    break
            except Exception:
                time.sleep(0.5)
        alice = _forge(1)
        harden = {**alice, "X-VF-Harden": "1"}

        # 1. The vuln fires by default (it IS the target).
        d = httpx.get(f"{ORIGIN}/api/projects/4", headers=alice, timeout=10).json()
        if d.get("project", {}).get("orgId") != 2:
            failures.append("BOLA does not fire by default in challenge mode")

        # 2. NO SIGNAL: the override header is ignored - the vuln still fires even
        #    when X-VF-Harden:1 is sent (in lab mode this would flip to 403/secure).
        h = httpx.get(f"{ORIGIN}/api/projects/4", headers=harden, timeout=10)
        if not (h.status_code == 200 and h.json().get("project", {}).get("orgId") == 2):
            failures.append("X-VF-Harden override is HONOURED in challenge mode (signal leak!)")

        # 3. No /api/secure/* routes anywhere in the OpenAPI.
        spec = httpx.get(f"{ORIGIN}/openapi.json", timeout=10).json()
        paths = list(spec.get("paths", {}))
        leaked = [p for p in paths if "/api/secure/" in p or p.endswith("-vuln") or "-loose" in p]
        if leaked:
            failures.append(f"answer-key route(s) exposed in OpenAPI: {leaked}")

        # 4. Shadow endpoints (hidden surface) are absent from the OpenAPI.
        if "/api/internal/integrations" in paths:
            failures.append("shadow endpoint /api/internal/integrations is in the OpenAPI")

    finally:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        else:
            proc.terminate()
        for s in ("", "-wal", "-shm"):
            (ROOT / f"{DB}{s}").unlink(missing_ok=True)

    if failures:
        print("[challenge] FAIL - answer-key signal detected:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("[challenge] PASS - challenge face leaks no signal "
          "(vulns fire by default, override ignored, no /secure routes, shadow hidden).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
