'use client'

import { useCallback, useEffect, useState } from 'react'
import { useApi } from '@/components/Providers'
import { Badge } from '@/components/Badge'

interface Catalog {
  plans: Record<string, { seats: number; priceCents: number }>
  creditPacks: Record<string, { credits: number; priceCents: number }>
}
interface Overview {
  plan: string
  creditBalance: number
  seats: { used: number; limit: number }
  catalog: Catalog
}
interface Order {
  id: string; kind: string; amountCents: number; discountCents: number
  credits: number; targetPlan: string | null; couponCode: string | null
  status: string; createdAt: string
}

const money = (c: number) => `$${(c / 100).toFixed(2)}`

const STATUS_TONE: Record<string, 'green' | 'slate' | 'amber' | 'red'> = {
  pending: 'amber', paid: 'amber', fulfilled: 'green', refunded: 'red', cancelled: 'slate',
}

export default function BillingPage() {
  const { apiFetch, ready } = useApi()
  const [ov, setOv] = useState<Overview | null>(null)
  const [orders, setOrders] = useState<Order[] | null>(null)
  const [isAdmin, setIsAdmin] = useState(false)
  const [coupon, setCoupon] = useState('')
  const [msg, setMsg] = useState('')

  const load = useCallback(async () => {
    const [o, ord, me] = await Promise.all([
      apiFetch('/api/billing'), apiFetch('/api/billing/orders'), apiFetch('/api/me'),
    ])
    if (o.ok) setOv(await o.json())
    if (ord.ok) setOrders((await ord.json()).orders)
    if (me.ok) { const m = await me.json(); setIsAdmin(m.isSuperAdmin || m.role === 'owner' || m.role === 'admin') }
  }, [apiFetch])

  useEffect(() => { if (ready) load() }, [ready, load])

  async function buy(body: object) {
    setMsg('')
    const r = await apiFetch('/api/billing/orders', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...body, couponCode: coupon || undefined }),
    })
    if (r.ok) { setCoupon(''); load() }
    else { const d = await r.json().catch(() => ({})); setMsg(`Order failed: ${d.detail ?? ''}`) }
  }

  async function act(o: Order, verb: 'pay' | 'fulfill' | 'refund') {
    setMsg('')
    const r = await apiFetch(`/api/billing/orders/${o.id}/${verb}`, { method: 'POST' })
    if (r.ok) load()
    else { const d = await r.json().catch(() => ({})); setMsg(`${verb} failed: ${d.detail ?? ''}`) }
  }

  if (!ov) return <p className="text-sm text-slate-400">Loading…</p>

  return (
    <div>
      <h1 className="text-2xl font-bold">Billing</h1>
      <p className="mt-1 text-slate-500">Manage your plan, seats, and credits.</p>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <p className="text-xs uppercase tracking-wide text-slate-400">Plan</p>
          <p className="mt-1 text-2xl font-bold capitalize text-slate-900">{ov.plan}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <p className="text-xs uppercase tracking-wide text-slate-400">Credit balance</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">{ov.creditBalance}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <p className="text-xs uppercase tracking-wide text-slate-400">Seats</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">{ov.seats.used} / {ov.seats.limit}</p>
        </div>
      </div>

      <section className="mt-8">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Buy</h2>
          <input
            value={coupon} onChange={(e) => setCoupon(e.target.value)} placeholder="Coupon code"
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>
        <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
          {Object.entries(ov.catalog.creditPacks).map(([key, p]) => (
            <div key={key} className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-4">
              <div>
                <p className="font-medium text-slate-900">{p.credits} credits</p>
                <p className="text-sm text-slate-500">{money(p.priceCents)}</p>
              </div>
              <button onClick={() => buy({ kind: 'credit_pack', pack: key })}
                className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700">Buy</button>
            </div>
          ))}
          {Object.entries(ov.catalog.plans).filter(([k]) => k !== 'starter' && k !== ov.plan).map(([key, p]) => (
            <div key={key} className="flex items-center justify-between rounded-lg border border-slate-200 bg-white p-4">
              <div>
                <p className="font-medium capitalize text-slate-900">{key} plan</p>
                <p className="text-sm text-slate-500">{money(p.priceCents)} · {p.seats} seats</p>
              </div>
              <button onClick={() => buy({ kind: 'plan_upgrade', plan: key })}
                className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700">Upgrade</button>
            </div>
          ))}
        </div>
      </section>

      {msg && <p className="mt-3 text-sm text-red-600">{msg}</p>}

      <section className="mt-8">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Order history</h2>
        {orders && orders.length === 0 && <p className="mt-3 text-sm text-slate-400">No orders yet.</p>}
        {orders && orders.length > 0 && (
          <ul className="mt-3 divide-y divide-slate-200 overflow-hidden rounded-lg border border-slate-200 bg-white">
            {orders.map((o) => (
              <li key={o.id} className="flex items-center justify-between px-5 py-3">
                <div className="min-w-0">
                  <p className="font-medium text-slate-900">
                    {o.kind === 'credit_pack' ? `${o.credits} credits` : `${o.targetPlan} plan`}
                    {o.couponCode && <span className="ml-2 text-xs text-green-700">({o.couponCode})</span>}
                  </p>
                  <p className="font-mono text-xs text-slate-400">{o.id} · {money(o.amountCents)}</p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Badge text={o.status} tone={STATUS_TONE[o.status] ?? 'slate'} />
                  {o.status === 'pending' && (
                    <button onClick={() => act(o, 'pay')} className="rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100">Pay</button>
                  )}
                  {o.status === 'paid' && (
                    <button onClick={() => act(o, 'fulfill')} className="rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100">Fulfill</button>
                  )}
                  {isAdmin && (o.status === 'paid' || o.status === 'fulfilled') && (
                    <button onClick={() => act(o, 'refund')} className="rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium text-red-600 hover:bg-red-50">Refund</button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
