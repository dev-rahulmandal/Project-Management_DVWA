"""
Outbound webhooks (the secure baseline).

An org registers a URL the server delivers signed event payloads to. The "test
delivery" endpoint performs a server-side POST to the registered URL - a classic
SSRF surface - so the secure handler validates the target host before fetching
(rejecting loopback / private / link-local / metadata addresses). The unfiltered
variant lives in vulns/webhook_ssrf.py.

Outbound deliveries are signed HMAC-SHA256 with the subscription secret, sent in
the `X-VF-Signature` header as `sha256=<hex>`.
"""
import hashlib
import hmac
import json
import secrets
from urllib.parse import urlparse

import aiosqlite
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ..auth import require_auth
from ..config import config
from ..db import get_db
from ..hardening import hardened
from .vulns.ssrf import _host_is_blocked   # reuse the SSRF allow/deny helper

router = APIRouter()

DELIVER_TIMEOUT = 5.0
KNOWN_EVENTS = {"order.paid", "task.created", "member.invited"}
CREDIT_EVENTS = {"invoice.paid", "payment.succeeded"}


def sign_body(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def inbound_sig_valid(body: bytes, signature: str | None) -> bool:
    """Constant-time check of an inbound provider signature over the raw body."""
    if not signature:
        return False
    expected = sign_body(config.WEBHOOK_INBOUND_SECRET, body)
    return hmac.compare_digest(signature, expected)


async def record_delivery(db, delivery_id: str, org_id: int, event: str) -> bool:
    """Record a provider delivery id; returns False if it was already seen."""
    try:
        await db.execute(
            "INSERT INTO webhook_deliveries (delivery_id, org_id, event) VALUES (?, ?, ?)",
            (delivery_id, org_id, event),
        )
    except aiosqlite.IntegrityError:
        return False
    return True


async def apply_billing_event(db, payload: dict) -> int:
    """Apply a (verified, de-duplicated) billing event; returns the new balance."""
    org_id = int(payload["orgId"])
    if payload.get("event") in CREDIT_EVENTS:
        await db.execute(
            "UPDATE organizations SET credit_balance = credit_balance + ? WHERE id = ?",
            (int(payload.get("credits", 0)), org_id),
        )
    await db.commit()
    async with db.execute(
        "SELECT credit_balance FROM organizations WHERE id = ?", (org_id,)
    ) as cur:
        row = await cur.fetchone()
    return row["credit_balance"] if row else 0


def _mask(secret: str) -> str:
    return secret[:8] + "…" if len(secret) > 8 else "…"


class WebhookCreate(BaseModel):
    url: str
    events: list[str] = []


async def _get_owned(db, webhook_id: int, org_id: int) -> dict:
    async with db.execute(
        "SELECT * FROM webhooks WHERE id = ? AND org_id = ?", (webhook_id, org_id)
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")
    return dict(row)


async def _deliver(url: str, secret: str, payload: dict) -> dict:
    import json
    body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", "X-VF-Signature": sign_body(secret, body)}
    async with httpx.AsyncClient(timeout=DELIVER_TIMEOUT, follow_redirects=False) as client:
        r = await client.post(url, content=body, headers=headers)
    return {"status": r.status_code, "responseBody": r.text[:2048]}


@router.post("/api/webhooks", status_code=201)
async def create_webhook(
    body: WebhookCreate,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    events = " ".join(e for e in body.events if e in KNOWN_EVENTS)
    secret = "whk_" + secrets.token_urlsafe(24)
    cur = await db.execute(
        "INSERT INTO webhooks (org_id, created_by_id, url, events, secret) "
        "VALUES (?, ?, ?, ?, ?)",
        (user["org_id"], user["id"], body.url, events, secret),
    )
    await db.commit()
    # Secret shown in full exactly once, at creation.
    return {"id": cur.lastrowid, "url": body.url, "events": events.split(), "secret": secret}


@router.get("/api/webhooks")
async def list_webhooks(
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT * FROM webhooks WHERE org_id = ? ORDER BY id DESC", (user["org_id"],)
    ) as cur:
        rows = await cur.fetchall()
    return {"webhooks": [{
        "id": r["id"], "url": r["url"], "events": (r["events"] or "").split(),
        "active": bool(r["active"]), "secret": _mask(r["secret"]),
    } for r in rows]}


@router.delete("/api/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    await _get_owned(db, webhook_id, user["org_id"])
    await db.execute("DELETE FROM webhooks WHERE id = ?", (webhook_id,))
    await db.commit()
    return {"ok": True}


@router.post("/api/webhooks/{webhook_id}/test")
async def test_webhook(
    request: Request,
    webhook_id: int,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    # WEBHOOK-SSRF-001 - one route; hardened() picks the path.
    wh = await _get_owned(db, webhook_id, user["org_id"])
    if hardened(request):
        # SECURE: validate the destination host before the server-side POST.
        parsed = urlparse(wh["url"])
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise HTTPException(status_code=400, detail="invalid_url")
        if _host_is_blocked(parsed.hostname):
            raise HTTPException(status_code=400, detail="blocked_target")
    try:
        # VULN (default): deliver to the registered URL with no host validation.
        return await _deliver(wh["url"], wh["secret"], {"event": "ping", "webhookId": webhook_id})
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"delivery_failed: {exc}")


# --------- INBOUND provider webhook - one route, two flaws by default ----------
# WEBHOOK-SIG-001 (signature verification fails open on a missing header) and
# WEBHOOK-REPLAY-001 (no idempotency) both live on this single endpoint.
#   hardened: require a valid HMAC signature AND enforce delivery-id idempotency.
#   default:  accept an UNSIGNED body (fail-open) AND re-apply replays (no dedup).
@router.post("/api/webhooks/inbound/billing")
async def inbound_billing(
    request: Request,
    db: aiosqlite.Connection = Depends(get_db),
):
    body = await request.body()
    sig = request.headers.get("X-VF-Signature")
    secure = hardened(request)

    if secure:
        if not inbound_sig_valid(body, sig):
            raise HTTPException(status_code=401, detail="invalid_signature")
    else:
        # WEBHOOK-SIG-001: fail open - only reject a signature that is PRESENT but wrong.
        if sig and not inbound_sig_valid(body, sig):
            raise HTTPException(status_code=401, detail="invalid_signature")

    try:
        payload = json.loads(body)
        delivery_id = str(payload["id"])
    except (json.JSONDecodeError, KeyError):
        raise HTTPException(status_code=400, detail="bad_payload")

    if secure:
        # WEBHOOK-REPLAY-001 control: enforce delivery-id idempotency.
        if not await record_delivery(db, delivery_id, int(payload["orgId"]), payload.get("event", "")):
            await db.commit()
            raise HTTPException(status_code=409, detail="replay_detected")
    # else: no idempotency - a replayed delivery is re-applied every time.

    balance = await apply_billing_event(db, payload)
    return {"ok": True, "creditBalance": balance}
