'use client'

import { useEffect } from 'react'
import Link from 'next/link'

// WEB-SECRET-001: a SECRET key is hardcoded in client code. Anything in a
// 'use client' module ships in the JS bundle the browser downloads, so this
// secret is recoverable by anyone via devtools / recon - secrets must never
// live client-side. The secured twin (/secure/pricing) keeps only a publishable
// key in the client and does secret operations on the server.
const PAYMENTS_SECRET_KEY = 'sk_live_VULNFORGE_FAKE_9f3a1c7b_DO_NOT_USE'

function initPayments(key: string): string {
  // Pretend SDK init - the point is the key is bundled regardless of use.
  return `payments-session-${key.slice(0, 10)}`
}

const TIERS = [
  { name: 'Starter', price: '$0', features: ['1 project', 'Community support'] },
  { name: 'Pro', price: '$29', features: ['Unlimited projects', 'Priority support', 'Audit log'] },
  { name: 'Enterprise', price: 'Contact us', features: ['SSO', 'Dedicated success', 'SLA'] },
]

export default function PricingPage() {
  useEffect(() => {
    // Dev mistake: initializing the payments SDK with the SECRET key client-side.
    void initPayments(PAYMENTS_SECRET_KEY)
  }, [])

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <Link href="/" className="text-sm text-brand-600 hover:underline">← Home</Link>
      <h1 className="mt-4 text-3xl font-bold">Pricing</h1>
      <p className="mt-2 text-slate-600">Plans for teams of every size.</p>
      <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-3">
        {TIERS.map((t) => (
          <div key={t.name} className="rounded-lg border border-slate-200 bg-white p-6">
            <h2 className="text-lg font-semibold">{t.name}</h2>
            <p className="mt-1 text-2xl font-bold text-brand-700">{t.price}</p>
            <ul className="mt-4 space-y-1 text-sm text-slate-600">
              {t.features.map((f) => <li key={f}>• {f}</li>)}
            </ul>
          </div>
        ))}
      </div>
    </div>
  )
}
