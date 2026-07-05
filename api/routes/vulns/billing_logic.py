import asyncio
import secrets

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ...auth import require_auth
from ...db import get_db
from ...hardening import hardened
from ..billing import CREDIT_PACKS, PLANS

router = APIRouter()


async def _order(db, public_id: str, org_id: int):
    async with db.execute(
        "SELECT * FROM orders WHERE public_id = ? AND org_id = ?", (public_id, org_id)
    ) as c:
        row = await c.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")
    return row


@router.get("/api/billing/orders/{public_id}")
async def order_detail(
    request: Request,
    public_id: str,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    row = await _order(db, public_id, user["org_id"])
    if hardened(request):
        return {"order": {
            "id":          row["public_id"],
            "kind":        row["kind"],
            "amountCents": row["amount_cents"],
            "status":      row["status"],
        }}
    return {"order": {
        "id":          row["public_id"],
        "internalId":  row["id"],
        "kind":        row["kind"],
        "amountCents": row["amount_cents"],
        "credits":     row["credits"],
        "status":      row["status"],
    }}


class RefundRequest(BaseModel):
    orderId: int | None = None
    amountCents: int | None = None
    orderPublicId: str | None = None


@router.post("/api/billing/refund")
async def refund(
    request: Request,
    body: RefundRequest,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    if hardened(request):
        if not body.orderPublicId:
            raise HTTPException(status_code=400, detail="order_public_id_required")
        row = await _order(db, body.orderPublicId, user["org_id"])
        if row["status"] not in ("paid", "fulfilled"):
            raise HTTPException(status_code=409, detail="invalid_transition")
        if row["status"] == "fulfilled" and row["kind"] == "credit_pack":
            await db.execute(
                "UPDATE organizations SET credit_balance = MAX(credit_balance - ?, 0) WHERE id = ?",
                (row["credits"], user["org_id"]),
            )
        await db.execute("UPDATE orders SET status = 'refunded' WHERE id = ?", (row["id"],))
        await db.commit()
        return {"refunded": True}

    if body.orderId is None or body.amountCents is None:
        raise HTTPException(status_code=400, detail="order_id_required")
    async with db.execute("SELECT id FROM orders WHERE id = ?", (body.orderId,)) as c:
        if await c.fetchone() is None:
            raise HTTPException(status_code=404, detail="not_found")
    await db.execute(
        "UPDATE organizations SET credit_balance = credit_balance + ? WHERE id = ?",
        (body.amountCents, user["org_id"]),
    )
    await db.commit()
    async with db.execute(
        "SELECT credit_balance FROM organizations WHERE id = ?", (user["org_id"],)
    ) as c:
        bal = (await c.fetchone())["credit_balance"]
    return {"refunded": True, "creditBalance": bal}


class OrderImport(BaseModel):
    kind: str
    status: str | None = None
    credits: int | None = None
    amountCents: int | None = None
    targetPlan: str | None = None


@router.post("/api/billing/orders/import", status_code=201)
async def import_order(
    body: OrderImport,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    status = body.status or "pending"
    credits = body.credits or 0
    amount = body.amountCents if body.amountCents is not None else 0
    target_plan = body.targetPlan
    public_id = "ord_" + secrets.token_urlsafe(12)
    cur = await db.execute(
        "INSERT INTO orders "
        "(public_id, org_id, created_by_id, kind, amount_cents, discount_cents, credits, target_plan, coupon_code, status) "
        "VALUES (?, ?, ?, ?, ?, 0, ?, ?, NULL, ?)",
        (public_id, user["org_id"], user["id"], body.kind, amount, credits, target_plan, status),
    )
    oid = cur.lastrowid
    if status == "fulfilled":
        if body.kind == "credit_pack":
            await db.execute(
                "UPDATE organizations SET credit_balance = credit_balance + ? WHERE id = ?",
                (credits, user["org_id"]),
            )
        elif body.kind == "plan_upgrade" and target_plan:
            await db.execute(
                "UPDATE organizations SET plan_tier = ? WHERE id = ?", (target_plan, user["org_id"])
            )
    await db.commit()
    async with db.execute("SELECT * FROM orders WHERE id = ?", (oid,)) as c:
        row = await c.fetchone()
    return {"order": {
        "id":          row["public_id"],
        "kind":        row["kind"],
        "amountCents": row["amount_cents"],
        "credits":     row["credits"],
        "status":      row["status"],
    }}


class QuickOrder(BaseModel):
    kind: str
    pack: str | None = None
    plan: str | None = None
    couponCode: str | None = None


@router.post("/api/billing/orders/quick", status_code=201)
async def quick_order(
    body: QuickOrder,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    if body.kind == "credit_pack":
        pack = CREDIT_PACKS.get(body.pack or "")
        if not pack:
            raise HTTPException(status_code=400, detail="invalid_pack")
        base, credits, target = pack["priceCents"], pack["credits"], None
    elif body.kind == "plan_upgrade":
        plan = PLANS.get(body.plan or "")
        if not plan or body.plan == "starter":
            raise HTTPException(status_code=400, detail="invalid_plan")
        base, credits, target = plan["priceCents"], 0, body.plan
    else:
        raise HTTPException(status_code=400, detail="invalid_kind")

    discount = 0
    if body.couponCode:
        async with db.execute(
            "SELECT discount_pct FROM coupons WHERE code = ?", (body.couponCode.strip(),)
        ) as c:
            row = await c.fetchone()
        if row is None:
            raise HTTPException(status_code=400, detail="invalid_coupon")
        discount = base * row["discount_pct"] // 100

    amount = max(base - discount, 0)
    public_id = "ord_" + secrets.token_urlsafe(12)
    cur = await db.execute(
        "INSERT INTO orders "
        "(public_id, org_id, created_by_id, kind, amount_cents, discount_cents, credits, target_plan, coupon_code, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')",
        (public_id, user["org_id"], user["id"], body.kind, amount, discount, credits,
         target, (body.couponCode or None)),
    )
    oid = cur.lastrowid
    await db.commit()
    async with db.execute("SELECT * FROM orders WHERE id = ?", (oid,)) as c:
        row = await c.fetchone()
    return {"order": {
        "id":            row["public_id"],
        "amountCents":   row["amount_cents"],
        "discountCents": row["discount_cents"],
        "status":        row["status"],
    }}


@router.post("/api/billing/orders/{public_id}/refund-credit")
async def refund_credit(
    request: Request,
    public_id: str,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    row = await _order(db, public_id, user["org_id"])
    if row["status"] != "paid":
        raise HTTPException(status_code=409, detail="invalid_transition")
    await asyncio.sleep(0.02)
    if hardened(request):
        cur = await db.execute(
            "UPDATE orders SET status = 'refunded' WHERE id = ? AND status = 'paid'", (row["id"],)
        )
        if cur.rowcount == 1:
            await db.execute(
                "UPDATE organizations SET credit_balance = credit_balance + ? WHERE id = ?",
                (row["credits"], user["org_id"]),
            )
        await db.commit()
        return {"granted": row["credits"] if cur.rowcount == 1 else 0}

    await db.execute(
        "UPDATE organizations SET credit_balance = credit_balance + ? WHERE id = ?",
        (row["credits"], user["org_id"]),
    )
    await db.execute("UPDATE orders SET status = 'refunded' WHERE id = ?", (row["id"],))
    await db.commit()
    return {"granted": row["credits"]}
