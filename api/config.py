import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

_ROOT = Path(__file__).parent.parent


class _Config:
    DB_PATH: Path = _ROOT / os.getenv("DATABASE_PATH", "prolane.db")

    JWT_SECRET: str = os.getenv("JWT_SECRET", "summer2023")
    JWT_ISSUER: str = os.getenv("JWT_ISSUER", "prolane-api")

    WEB_ORIGIN: str = os.getenv("WEB_ORIGIN", "http://localhost:8082")
    WEB_ORIGINS: list = [
        o.strip() for o in os.getenv("WEB_ORIGIN", "http://localhost:8082").split(",") if o.strip()
    ]

    UPLOAD_DIR: Path = _ROOT / os.getenv("UPLOAD_DIR", "uploads")

    SCIM_TOKEN: str = os.getenv("SCIM_TOKEN", "scim_pt_9Qf2Ht7kLm3Rd8vB1nX")
    SCIM_ORG_ID: int = int(os.getenv("SCIM_ORG_ID", "1"))

    WEBHOOK_INBOUND_SECRET: str = os.getenv(
        "WEBHOOK_INBOUND_SECRET", "whsec_demo_billing_5b2e9f1c")

    PORT: int = int(os.getenv("API_PORT", "8081"))

    VF_HARDENED: bool = os.getenv("VF_HARDENED", "0") == "1"
    VF_LAB: bool = os.getenv("VF_LAB", "0") == "1"


config = _Config()
