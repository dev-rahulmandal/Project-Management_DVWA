"""
Billing: credit packs, plan upgrades, and a server-enforced order state machine.

This is the SECURE baseline for the business-logic thrust:
  - prices come from the server-side CATALOG, never the request body,
  - state transitions are validated (pending -> paid -> fulfilled; refund only
    from paid/fulfilled; no skipping/replay),
  - coupons are single-use, decremented atomically,
  - orders are addressed by an opaque public_id, everything is org-scoped,
  - refunds reverse the effect and are admin-gated.
Intentional business-logic-abuse variants (price/mass-assignment, refund
inflation chain, coupon-reuse, quota bypass, double-refund race) are added later
as separate, manifested endpoints.
"""
import secrets

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import require_admin, require_auth
from ..db import get_db

router = APIRouter()

PLANS = {
    "starter":    {"seats": 2,   "priceCents": 0},
    "pro":        {"seats": 10,  "priceCents": 2900},
    "enterprise": {"seats": 100, "priceCents": 9900},
}
CREDIT_PACKS = {
    "small": {"credits": 100, "priceCents": 900},
    "large": {"credits": 500, "priceCents": 3900},
}


def present_order(row) -> dict:
    return {
        "id":            row["public_id"],   # opaque id only - never the int PK
        "kind":          row["kind"],
        "amountCents":   row["amount_cents"],
        "discountCents": row["discount_cents"],
        "credits":       row["credits"],
        "targetPlan":    row["target_plan"],
        "couponCode":    row["coupon_code"],
        "status":        row["status"],
        "createdAt":     row["created_at"],
    }


async def _org(db, org_id: int):
    async with db.execute("SELECT * FROM organizations WHERE id = ?", (org_id,)) as c:
        return await c.fetchone()


async def _order(db, public_id: str, org_id: int):
    async with db.execute(
        "SELECT * FROM orders WHERE public_id = ? AND org_id = ?", (public_id, org_id)
    ) as c:
        row = await c.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")
    return row


@router.get("/api/billing")
async def billing_overview(
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    org = await _org(db, user["org_id"])
    async with db.execute(
        "SELECT COUNT(*) AS c FROM users WHERE org_id = ? AND is_active = 1", (user["org_id"],)
    ) as cur:
        members = (await cur.fetchone())["c"]
    plan = org["plan_tier"]
    return {
        "plan":          plan,
        "creditBalance": org["credit_balance"],
        "seats":         {"used": members, "limit": PLANS.get(plan, {}).get("seats", 0)},
        "catalog":       {"plans": PLANS, "creditPacks": CREDIT_PACKS},
    }


@router.get("/api/billing/orders")
async def list_orders(
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    async with db.execute(
        "SELECT * FROM orders WHERE org_id = ? ORDER BY id DESC", (user["org_id"],)
    ) as cur:
        rows = await cur.fetchall()
    return {"orders": [present_order(r) for r in rows]}


class OrderCreate(BaseModel):
    kind: str
    pack: str | None = None
    plan: str | None = None
    couponCode: str | None = None


async def _apply_coupon(db, code: str, base_cents: int) -> int:
    async with db.execute(
        "SELECT discount_pct FROM coupons WHERE code = ?", (code,)
    ) as cur:
        row = await cur.fetchone()
    if row is None:
        raise HTTPException(status_code=400, detail="invalid_coupon")
    # Atomic single-use decrement.
    cur = await db.execute(
        "UPDATE coupons SET remaining_uses = remaining_uses - 1 "
        "WHERE code = ? AND remaining_uses > 0", (code,)
    )
    if cur.rowcount == 0:
        raise HTTPException(status_code=400, detail="coupon_exhausted")
    return base_cents * row["discount_pct"] // 100


@router.post("/api/billing/orders", status_code=201)
async def create_order(
    body: OrderCreate,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    # Price is taken from the server catalog - never from the request.
    if body.kind == "credit_pack":
        pack = CREDIT_PACKS.get(body.pack or "")
        if not pack:
            raise HTTPException(status_code=400, detail="invalid_pack")
        base, credits, target_plan = pack["priceCents"], pack["credits"], None
    elif body.kind == "plan_upgrade":
        plan = PLANS.get(body.plan or "")
        if not plan or body.plan == "starter":
            raise HTTPException(status_code=400, detail="invalid_plan")
        base, credits, target_plan = plan["priceCents"], 0, body.plan
    else:
        raise HTTPException(status_code=400, detail="invalid_kind")

    discount = 0
    if body.couponCode:
        discount = await _apply_coupon(db, body.couponCode.strip(), base)
    amount = max(base - discount, 0)

    public_id = "ord_" + secrets.token_urlsafe(12)
    cur = await db.execute(
        "INSERT INTO orders "
        "(public_id, org_id, created_by_id, kind, amount_cents, discount_cents, credits, target_plan, coupon_code, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')",
        (public_id, user["org_id"], user["id"], body.kind, amount, discount, credits,
         target_plan, (body.couponCode or None)),
    )
    oid = cur.lastrowid
    await db.commit()
    async with db.execute("SELECT * FROM orders WHERE id = ?", (oid,)) as c:
        return {"order": present_order(await c.fetchone())}


@router.post("/api/billing/orders/{public_id}/pay")
async def pay_order(
    public_id: str,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    row = await _order(db, public_id, user["org_id"])
    if row["status"] != "pending":
        raise HTTPException(status_code=409, detail="invalid_transition")
    await db.execute("UPDATE orders SET status = 'paid' WHERE id = ?", (row["id"],))
    await db.commit()
    return {"order": present_order(await _order(db, public_id, user["org_id"]))}


@router.post("/api/billing/orders/{public_id}/fulfill")
async def fulfill_order(
    public_id: str,
    user: dict = Depends(require_auth),
    db: aiosqlite.Connection = Depends(get_db),
):
    row = await _order(db, public_id, user["org_id"])
    if row["status"] != "paid":
        raise HTTPException(status_code=409, detail="invalid_transition")
    if row["kind"] == "credit_pack":
        await db.execute(
            "UPDATE organizations SET credit_balance = credit_balance + ? WHERE id = ?",
            (row["credits"], user["org_id"]),
        )
    elif row["kind"] == "plan_upgrade" and row["target_plan"]:
        await db.execute(
            "UPDATE organizations SET plan_tier = ? WHERE id = ?",
            (row["target_plan"], user["org_id"]),
        )
    await db.execute("UPDATE orders SET status = 'fulfilled' WHERE id = ?", (row["id"],))
    await db.commit()
    return {"order": present_order(await _order(db, public_id, user["org_id"]))}


@router.post("/api/billing/orders/{public_id}/refund")
async def refund_order(
    public_id: str,
    user: dict = Depends(require_admin),
    db: aiosqlite.Connection = Depends(get_db),
):
    row = await _order(db, public_id, user["org_id"])
    if row["status"] not in ("paid", "fulfilled"):
        raise HTTPException(status_code=409, detail="invalid_transition")
    if row["status"] == "fulfilled" and row["kind"] == "credit_pack":
        await db.execute(
            "UPDATE organizations SET credit_balance = MAX(credit_balance - ?, 0) WHERE id = ?",
            (row["credits"], user["org_id"]),
        )
    await db.execute("UPDATE orders SET status = 'refunded' WHERE id = ?", (row["id"],))
    await db.commit()
    return {"order": present_order(await _order(db, public_id, user["org_id"]))}
