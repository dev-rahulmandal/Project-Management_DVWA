"""
The challenge catalog - the SAFE, learner-facing view of the 42 intentional
vulns, derived from the ground-truth manifest. It NEVER exposes the answer key
(endpoint / repro / detector / gating / secured_twin); only class-level identity
that gets revealed once a vuln is solved.
"""
from __future__ import annotations

from pathlib import Path

import yaml

_MANIFEST = Path(__file__).resolve().parent.parent / "ground-truth" / "manifest.yaml"

_CATEGORY = {
    "BOLA": "Access control",
    "BrokenObjectLevelAuthorization": "Access control",
    "BFLA": "Access control",
    "BrokenFunctionLevelAuthorization": "Access control",
    "BrokenFunctionAuthorization": "Access control",
    "BrokenObjectPropertyLevelAuthorization": "Access control",
    "ExcessiveDataExposure": "Access control",
    "MassAssignment": "Access control",
    "SQLInjection": "Injection",
    "SSTI": "Injection",
    "CommandInjection": "Injection",
    "InsecureDeserialization": "Injection",
    "PathTraversal": "Injection",
    "SSRF": "SSRF",
    "BrokenAuthentication": "Auth & tokens",
    "JWTSignatureBypass": "Auth & tokens",
    "PredictableToken": "Auth & tokens",
    "BruteForce": "Auth & tokens",
    "ImproperAuthentication": "Auth & tokens",
    "RaceCondition": "Business logic",
    "BusinessLogicAbuse": "Business logic",
    "StoredXSS": "Client & web",
    "DOMXSS": "Client & web",
    "SecretsInBundle": "Client & web",
    "PrototypePollution": "Client & web",
    "Clickjacking": "Client & web",
    "OpenRedirect": "Client & web",
    "CORSMisconfiguration": "Misconfiguration",
    "SecurityMisconfiguration": "Misconfiguration",
    "ResourceConsumption": "Misconfiguration",
}


def load_catalog() -> list[dict]:
    """Safe subset of the intentional vulns (drops secured twins + decoys)."""
    doc = yaml.safe_load(_MANIFEST.read_text(encoding="utf-8")) or {}
    out = []
    for e in doc.get("entries", []):
        if not e.get("intentional") or e.get("decoy"):
            continue
        vclass = e.get("class", "")
        out.append({
            "id": e["id"],
            "title": e["title"],
            "category": _CATEGORY.get(vclass, "Other"),
            "severity": e.get("severity", "Medium"),
            "owasp": e.get("owasp") or "",
            "origin": e.get("origin") or "",
        })
    return out
