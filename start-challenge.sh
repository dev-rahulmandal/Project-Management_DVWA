#!/usr/bin/env bash
# ============================================================================
#  VulnForge CHALLENGE launcher (Linux / macOS) - the hard target (no signal).
#  Same code as start-dev.sh, but VF_LAB=0 so:
#    - every vuln fires by DEFAULT (it IS the target), and
#    - the X-VF-Harden override is IGNORED (a tester can't flip to the secure
#      twin), and the /secure/* pages are hidden.
#  Use start-dev.sh for the LAB face (manual verification + `make verify`).
#  Verify there is no leak first:   python3 tools/challenge_check.py
#  Usage:  ./start-challenge.sh   (or: bash start-challenge.sh)
#  Expose to another machine (e.g. a Windows host -> this VM):
#     VF_HOST=<vm-ip> ./start-challenge.sh                    (IP:port, or VF_HOST=auto)
#     VF_HOST=vulnforge.test VF_API_HOST=api.vulnforge.test ./start-challenge.sh
#       (hostnames -> add a matching entry to the client's hosts file)
#
#  Self-bootstrapping: installs everything it needs on first run -
#    - Node.js + npm (via apt/dnf/pacman/zypper/brew; uses sudo on Linux),
#    - a project-local .venv (gitignored) with the Python deps,
#    - the web node_modules, then a production web build.
#  Python lives in .venv so we never fight a PEP-668 externally-managed system
#  Python (Kali/Debian). Installing Node needs root → you'll see a sudo prompt.
# ============================================================================
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PY=python3; command -v python3 >/dev/null 2>&1 || PY=python

# --- the challenge face: vulnerable by default, override OFF -----------------
# Exported, so both the api and web child processes inherit it.
export VF_HARDENED=0
export VF_LAB=0

echo "[VulnForge] CHALLENGE FACE (VF_LAB=0) - vulns live, no answer-key signal"
echo "[VulnForge] root : $ROOT"

# --- detect sudo + package manager (used for auto-install) ------------------
SUDO=""
if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1; then SUDO="sudo"; fi
PM=""
for c in apt-get dnf pacman zypper brew; do
  command -v "$c" >/dev/null 2>&1 && { PM="$c"; break; }
done

# --- network exposure (opt-in; default = localhost only, per safety rule) ---
# VF_HOST     = host/IP the OTHER machine uses to reach this VM (IP, hostname, or "auto").
# VF_API_HOST = extra hostname alias for the api (optional; defaults to VF_HOST).
# In network mode we bind 0.0.0.0, allow the app's login from localhost + the LAN IP
# + your hostname all at once, and bake the api origin to the LAN IP (reachable from
# both the host and the VM). Exported BEFORE the web build so the api origin bakes in.
BIND="127.0.0.1"
VM_IP=""; WEB_HOST=""; API_HOST_NAME=""; API_PUB=""; HOST_NAMES=""
if [ -n "${VF_HOST:-}" ]; then
  BIND="0.0.0.0"
  VM_IP="$(ip route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}')"
  [ -z "$VM_IP" ] && VM_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
  if [ "$VF_HOST" = "auto" ]; then
    [ -z "$VM_IP" ] && { echo "[VulnForge] ERROR: could not auto-detect a LAN IP - set VF_HOST=<ip> explicitly."; exit 1; }
    WEB_HOST="$VM_IP"
  else
    WEB_HOST="$VF_HOST"
  fi
  API_HOST_NAME="${VF_API_HOST:-$WEB_HOST}"
  # the SPA bakes ONE api origin; the LAN IP is reachable from the host and on the VM.
  API_PUB="${VM_IP:-$WEB_HOST}"
  export NEXT_PUBLIC_API_ORIGIN="http://$API_PUB:8081"
  # login + CORS allow-list: localhost + LAN IP + hostname (deduped, non-empty).
  origins=""
  for o in "http://localhost:8082" "${VM_IP:+http://$VM_IP:8082}" "http://$WEB_HOST:8082"; do
    [ -z "$o" ] && continue
    case ",$origins," in *",$o,"*) continue;; esac
    origins="${origins:+$origins,}$o"
  done
  export WEB_ORIGIN="$origins"
  # hostnames (non-IP) that need a hosts-file entry on the client machine
  for h in "$WEB_HOST" "$API_HOST_NAME"; do
    case "$h" in
      *[!0-9.]*)
        case " $HOST_NAMES " in *" $h "*) : ;; *) HOST_NAMES="${HOST_NAMES:+$HOST_NAMES }$h";; esac ;;
    esac
  done
fi

# --- access-points panel (printed once both servers are launching) ----------
print_access_panel() {
  echo ""
  echo "  == VulnForge access points ================================="
  if [ "$BIND" != "0.0.0.0" ]; then
    echo "    web  http://localhost:8082       api  http://localhost:8081"
    echo "    (localhost-only; set VF_HOST=<vm-ip|hostname> or VF_HOST=auto to expose)"
    echo "  ============================================================"
    return
  fi
  echo "    web  (open any of these in a browser; login works on all):"
  _seen=""
  for h in "localhost" "$VM_IP" "$WEB_HOST"; do
    [ -z "$h" ] && continue
    case ",$_seen," in *",$h,"*) continue;; esac
    _seen="$_seen,$h"; printf "      http://%s:8082\n" "$h"
  done
  echo "    api  (the app uses the first; all reachable for curl/tools):"
  _seen=""
  for h in "$API_PUB" "localhost" "$VM_IP" "$API_HOST_NAME"; do
    [ -z "$h" ] && continue
    case ",$_seen," in *",$h,"*) continue;; esac
    _seen="$_seen,$h"; printf "      http://%s:8081\n" "$h"
  done
  if [ -n "$HOST_NAMES" ]; then
    echo ""
    echo "    Windows hosts file - C:\\Windows\\System32\\drivers\\etc\\hosts (one line):"
    printf "      %s   %s\n" "${VM_IP:-<vm-ip>}" "$HOST_NAMES"
  fi
  echo "  ============================================================"
}

# --- ensure Node.js >= 18.17 (required by Next 14) --------------------------
node_ok() {
  command -v node >/dev/null 2>&1 || return 1
  local v maj min
  v="$(node -p 'process.versions.node' 2>/dev/null)" || return 1
  maj="${v%%.*}"; min="${v#*.}"; min="${min%%.*}"
  [ "$maj" -gt 18 ] && return 0
  [ "$maj" -eq 18 ] && [ "$min" -ge 17 ] && return 0
  return 1
}
ensure_node() {
  if command -v npm >/dev/null 2>&1 && node_ok; then return 0; fi
  echo "[VulnForge] Node.js >= 18.17 (for Next 14) not found - installing via ${PM:-?}..."
  case "$PM" in
    apt-get) $SUDO apt-get update -qq && $SUDO apt-get install -y nodejs npm ;;
    dnf)     $SUDO dnf install -y nodejs npm ;;
    pacman)  $SUDO pacman -Sy --noconfirm nodejs npm ;;
    zypper)  $SUDO zypper install -y nodejs npm ;;
    brew)    brew install node ;;
    *)       echo "[VulnForge]   no supported package manager (apt/dnf/pacman/zypper/brew)." ;;
  esac
}
ensure_node || true
if ! command -v npm >/dev/null 2>&1 || ! node_ok; then
  echo "[VulnForge] ERROR: Node.js >= 18.17 still unavailable."
  echo "[VulnForge]   Your distro's package may be too old. Install a current Node via nvm, or nodesource:"
  echo "[VulnForge]     curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs"
  exit 1
fi

# --- free ports 8082/8081 ---------------------------------------------------
free_port() {
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "$1/tcp" >/dev/null 2>&1 || true
  elif command -v lsof >/dev/null 2>&1; then
    lsof -ti "tcp:$1" 2>/dev/null | xargs -r kill -9 2>/dev/null || true
  fi
}
free_port 8082; free_port 8081

# --- python venv: isolate api deps (sidesteps PEP-668 externally-managed) ---
VENV="$ROOT/.venv"
VPY="$VENV/bin/python"
if [ ! -x "$VPY" ]; then
  echo "[VulnForge] creating virtualenv (.venv)..."
  "$PY" -m venv "$VENV" 2>/dev/null || {
    echo "[VulnForge] installing python venv support..."
    [ "$PM" = "apt-get" ] && $SUDO apt-get install -y python3-venv python3-pip
    "$PY" -m venv "$VENV" || {
      echo "[VulnForge] ERROR: could not create .venv (try: sudo apt install python3-venv)."
      exit 1
    }
  }
fi
# (Re)install if any dependency is missing. jose is the canary: Kali ships
# uvicorn+fastapi system-wide but not python-jose, which masked the gap before.
"$VPY" -c "import uvicorn, fastapi, jose, bcrypt, aiosqlite, httpx, jinja2, dotenv, multipart" 2>/dev/null || {
  echo "[VulnForge] installing Python dependencies into .venv..."
  "$VPY" -m pip install -q --upgrade pip
  "$VPY" -m pip install -r api/requirements.txt
}

# --- ensure web deps --------------------------------------------------------
[ -d web/node_modules ] || ( cd web && npm install )

# --- build the web once so /secure/* gating runs in production --------------
echo "[VulnForge] building web (challenge face)..."
( cd web && npm run build )

# --- launch both in challenge mode; Ctrl-C stops both -----------------------
echo "[VulnForge] starting api (:8081) + web (:8082) in challenge mode..."
"$VPY" -m uvicorn api.main:app --host "$BIND" --port 8081 &
API_PID=$!
( cd web && npm run start -- -H "$BIND" ) &
WEB_PID=$!

cleanup() {
  echo; echo "[VulnForge] stopping..."
  kill "$API_PID" "$WEB_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

echo "[VulnForge] CHALLENGE up."
print_access_panel
wait
