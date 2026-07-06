"""Prolane launcher - one cross-platform command to install and run.

Usage:
    python run.py               start the challenge face (realistic target, no answer-key signal)
    python run.py --lab         start the lab face (answer-key signals, secure twins, /docs open)

On first run it installs the Python and web dependencies and seeds the local
.env files from the checked-in examples. Ctrl-C stops both servers.
Requires Python 3.11+ and Node.js 18.17+ (for Next.js 14).
"""
import sys

if sys.version_info < (3, 11):
    sys.stderr.write(
        "[prolane] Python 3.11+ is required (found %s).\n"
        "  Install it from https://www.python.org/downloads/ and run again.\n"
        % sys.version.split()[0]
    )
    raise SystemExit(1)

import argparse
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
REQ = ROOT / "api" / "requirements.txt"
API_PORT, WEB_PORT = 8081, 8082
IS_WIN = os.name == "nt"
CANARY = ["uvicorn", "fastapi", "jose", "jwt", "bcrypt", "aiosqlite", "httpx", "jinja2", "dotenv", "multipart"]


def die(msg: str) -> None:
    sys.stderr.write("[prolane] ERROR: " + msg + "\n")
    raise SystemExit(1)


def _run(cmd, **kw) -> int:
    return subprocess.run(cmd, **kw).returncode


def _deps_ok(python: str) -> bool:
    return subprocess.run([python, "-c", "import " + ", ".join(CANARY)], capture_output=True).returncode == 0


def _pip_ok(python: str) -> bool:
    return subprocess.run([python, "-m", "pip", "--version"], capture_output=True).returncode == 0


def ensure_python() -> str:
    """Return an interpreter that has the api deps, installing them if needed."""
    if _deps_ok(sys.executable):
        return sys.executable
    if not REQ.exists():
        die("api/requirements.txt not found - are you running this from the repo root?")
    # Prefer installing into the current interpreter.
    if _pip_ok(sys.executable):
        print("[prolane] installing Python dependencies...")
        if _run([sys.executable, "-m", "pip", "install", "-r", str(REQ)]) == 0 and _deps_ok(sys.executable):
            return sys.executable
        print("[prolane] direct install did not take (likely an externally-managed Python) - using a .venv...")
    else:
        print("[prolane] pip is unavailable for this Python - using a .venv...")
    return _install_in_venv()


def _install_in_venv() -> str:
    venv = ROOT / ".venv"
    vpy = venv / ("Scripts/python.exe" if IS_WIN else "bin/python")
    if not vpy.exists():
        print("[prolane] creating .venv (isolated environment)...")
        if _run([sys.executable, "-m", "venv", str(venv)]) != 0 or not vpy.exists():
            die(
                "could not create a virtualenv.\n"
                "  - Debian/Ubuntu/Kali: sudo apt install -y python3-venv python3-pip\n"
                "  - then run again: python run.py"
            )
    if not _pip_ok(str(vpy)):
        die("the .venv has no pip. Delete the .venv folder and run again.")
    _run([str(vpy), "-m", "pip", "install", "-q", "--upgrade", "pip"])
    if _run([str(vpy), "-m", "pip", "install", "-r", str(REQ)]) != 0 or not _deps_ok(str(vpy)):
        die(
            "failed to install the Python dependencies.\n"
            "  - check your internet connection, then run again, or install manually:\n"
            "      %s -m pip install -r api/requirements.txt" % vpy
        )
    return str(vpy)


def ensure_node() -> None:
    if shutil.which("node") is None or shutil.which("npm") is None:
        die(
            "Node.js 18.17+ and npm are required (for Next.js 14).\n"
            "  Install from https://nodejs.org/ (or via nvm), then run again."
        )
    try:
        ver = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip().lstrip("v")
        major, minor = (int(x) for x in ver.split(".")[:2])
        if (major, minor) < (18, 17):
            die("Node.js 18.17+ is required (for Next.js 14), found %s. Upgrade Node and run again." % ver)
    except (ValueError, IndexError):
        pass  # unparseable version string - let next fail with its own message
    if not (WEB / "node_modules").exists():
        print("[prolane] installing web dependencies (first run, may take a minute)...")
        if _run("npm install", cwd=WEB, shell=True) != 0:
            die("npm install failed. Check your network, then run again (or: cd web && npm install).")


def seed_env() -> None:
    for example, target in [
        (ROOT / "api" / ".env.example", ROOT / "api" / ".env"),
        (WEB / ".env.example", WEB / ".env.local"),
    ]:
        if example.exists() and not target.exists():
            shutil.copyfile(example, target)
            print("[prolane] seeded %s from %s" % (target.relative_to(ROOT).as_posix(), example.name))


def free_port(port: int) -> None:
    try:
        if IS_WIN:
            out = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "Get-NetTCPConnection -State Listen -LocalPort %d -ErrorAction SilentlyContinue"
                 " | Select-Object -ExpandProperty OwningProcess -Unique" % port],
                capture_output=True, text=True).stdout
            for pid in out.split():
                subprocess.run(["taskkill", "/F", "/T", "/PID", pid.strip()], capture_output=True)
        else:
            out = subprocess.run(
                ["bash", "-c", "lsof -ti tcp:%d 2>/dev/null || fuser %d/tcp 2>/dev/null" % (port, port)],
                capture_output=True, text=True).stdout
            for pid in out.split():
                subprocess.run(["kill", "-9", pid.strip()], capture_output=True)
    except Exception:
        pass


def main() -> None:
    ap = argparse.ArgumentParser(description="Prolane launcher")
    ap.add_argument("--lab", "--dev", dest="lab", action="store_true",
                    help="run the lab face (VF_LAB=1: answer-key signals, secure twins, /docs). Default is the challenge face.")
    args = ap.parse_args()

    api_py = ensure_python()
    ensure_node()
    seed_env()

    env = dict(os.environ)
    env["PROLANE_NO_BANNER"] = "1"
    env["VF_LAB"] = "1" if args.lab else "0"
    face = "LAB" if args.lab else "CHALLENGE"

    print("[prolane] freeing ports %d/%d if in use..." % (API_PORT, WEB_PORT))
    free_port(API_PORT)
    free_port(WEB_PORT)

    api_cmd = [api_py, "-m", "uvicorn", "api.main:app", "--port", str(API_PORT)]
    if args.lab:
        api_cmd.append("--reload")

    print("[prolane] starting %s:  api http://localhost:%d   web http://localhost:%d" % (face, API_PORT, WEB_PORT))

    sys.path.insert(0, str(ROOT))
    from api.banner import render_banner
    _runtime = "Local dev via run.py --lab (hot-reload)" if args.lab else "Local via run.py (challenge face)"
    print(render_banner(
        args.lab, env.get("VF_HARDENED", "0") == "1", _runtime,
        "http://localhost:%d" % WEB_PORT, "http://localhost:%d" % API_PORT, "Ctrl-C"), flush=True)

    flags = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if IS_WIN else {"start_new_session": True}
    try:
        procs = [
            subprocess.Popen(api_cmd, cwd=str(ROOT), env=env, **flags),
            subprocess.Popen("npm run dev", cwd=str(WEB), env=env, shell=True, **flags),
        ]
    except OSError as exc:
        die("could not start the servers: %s" % exc)

    def stop(*_):
        print("\n[prolane] stopping...")
        for p in procs:
            try:
                if IS_WIN:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
                else:
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            except Exception:
                pass
        raise SystemExit(0)

    signal.signal(signal.SIGINT, stop)
    if not IS_WIN:
        signal.signal(signal.SIGTERM, stop)
    try:
        while True:
            for p in procs:
                if p.poll() is not None:
                    print("[prolane] a server exited (code %s) - shutting down the other." % p.returncode)
                    stop()
            time.sleep(1)
    except KeyboardInterrupt:
        stop()


if __name__ == "__main__":
    main()
