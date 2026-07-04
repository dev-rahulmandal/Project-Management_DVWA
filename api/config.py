import os
from pathlib import Path
from dotenv import load_dotenv

# Load from api/.env if present; fall back to environment
load_dotenv(Path(__file__).parent / ".env")

_ROOT = Path(__file__).parent.parent  # project root (VulnForge/)


class _Config:
    # Database file path - always resolved relative to project root
    DB_PATH: Path = _ROOT / os.getenv("DATABASE_PATH", "vulnforge.db")

    # JWT - deliberately weak default to support AUTH-JWT-WEAK vuln
    JWT_SECRET: str = os.getenv("JWT_SECRET", "changeme")
    JWT_ISSUER: str = os.getenv("JWT_ISSUER", "vulnforge-api")

    # CORS: the allowed web origin(s). WEB_ORIGIN may be a comma-separated list so
    # network mode can expose the app under localhost + the LAN IP + a hostname at
    # once; a single value behaves exactly as before (verify suite unaffected).
    WEB_ORIGIN: str = os.getenv("WEB_ORIGIN", "http://localhost:8082")
    WEB_ORIGINS: list = [
        o.strip() for o in os.getenv("WEB_ORIGIN", "http://localhost:8082").split(",") if o.strip()
    ]

    # Where uploaded attachments are stored on disk (runtime, gitignored)
    UPLOAD_DIR: Path = _ROOT / os.getenv("UPLOAD_DIR", "uploads")

    # SCIM 2.0 provisioning bearer (the IdP integration credential). Fake/obvious -
    # represents a lower-trust automation token configured at the identity provider,
    # NOT an interactive admin session. Bound to the acme org (id 1) below.
    SCIM_TOKEN: str = os.getenv("SCIM_TOKEN", "vfscim_demo_8c1d4e7a2b")
    SCIM_ORG_ID: int = int(os.getenv("SCIM_ORG_ID", "1"))

    # Shared HMAC secret for INBOUND provider webhooks (e.g. the billing provider
    # signs delivery bodies with this). Fake/obvious - training only.
    WEBHOOK_INBOUND_SECRET: str = os.getenv(
        "WEBHOOK_INBOUND_SECRET", "whsec_demo_billing_5b2e9f1c")

    PORT: int = int(os.getenv("API_PORT", "8081"))

    # --- Two-face build split (Phase A "kill the tells") -----------------------
    # Each catalogued vuln lives at ONE neutrally-named route; whether it behaves
    # vulnerably or securely is decided at runtime by `hardened()` (api/hardening.py),
    # NOT by a -vuln/-SAFE route suffix. The CHALLENGE deployment runs with
    # VF_HARDENED=0 (vulnerable by default) and VF_LAB=0 (no test override) so the
    # target carries zero signal. The LAB/verify harness runs with VF_LAB=1, which
    # lets a per-request override (header X-VF-Harden / WS ?harden=) exercise BOTH
    # faces against one running stack - so the control test proves the secure path
    # holds without a separate route or a restart.
    VF_HARDENED: bool = os.getenv("VF_HARDENED", "0") == "1"   # default: vulnerable
    VF_LAB: bool = os.getenv("VF_LAB", "1") == "1"             # default: lab (override on)


config = _Config()
