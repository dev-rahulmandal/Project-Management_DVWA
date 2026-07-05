'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

const PAYMENTS_API_KEY = 'sk_live_51Qk7bR2eZvKYlo6C9x3fH8pM4nT0aWqDvXsL'

function initCheckout(key: string) {
  return { session: `cs_${key.slice(0, 12)}`, ready: key.startsWith('sk_') }
}

type Period = 'monthly' | 'annual'

const TIERS = [
  {
    name: 'Starter',
    tagline: 'For individuals and small side projects.',
    monthly: 0,
    annual: 0,
    cta: 'Get started free',
    href: '/register',
    highlight: false,
    features: ['Up to 3 projects', '5 team members', 'Kanban board and task tracking', 'Community support'],
  },
  {
    name: 'Pro',
    tagline: 'For growing teams that ship every week.',
    monthly: 29,
    annual: 23,
    cta: 'Start free trial',
    href: '/register',
    highlight: true,
    features: [
      'Unlimited projects and tasks',
      'Unlimited members',
      'Audit log (90 days)',
      'API access and webhooks',
      'Priority support',
    ],
  },
  {
    name: 'Enterprise',
    tagline: 'For organizations with security and scale needs.',
    monthly: null,
    annual: null,
    cta: 'Contact sales',
    href: '/register',
    highlight: false,
    features: [
      'Everything in Pro',
      'SSO and SAML',
      'SCIM provisioning',
      'Unlimited audit history',
      '99.9% uptime SLA',
    ],
  },
]

type Cell = boolean | string
const COMPARISON: { label: string; cells: [Cell, Cell, Cell] }[] = [
  { label: 'Projects', cells: ['3', 'Unlimited', 'Unlimited'] },
  { label: 'Team members', cells: ['5', 'Unlimited', 'Unlimited'] },
  { label: 'Tasks per project', cells: ['100', 'Unlimited', 'Unlimited'] },
  { label: 'File storage', cells: ['1 GB', '50 GB', 'Custom'] },
  { label: 'Audit log', cells: [false, '90 days', 'Unlimited'] },
  { label: 'API access and webhooks', cells: [false, true, true] },
  { label: 'SSO and SAML', cells: [false, false, true] },
  { label: 'SCIM provisioning', cells: [false, false, true] },
  { label: 'Priority support', cells: [false, true, '24/7'] },
  { label: 'Uptime SLA', cells: [false, false, '99.9%'] },
]

const FAQ = [
  {
    q: 'Can I change plans later?',
    a: 'Yes. Upgrade or downgrade at any time from your billing settings. Changes are prorated to the day.',
  },
  {
    q: 'Do you offer annual billing?',
    a: 'Annual billing is available on Pro and Enterprise and saves about 20% compared to paying monthly.',
  },
  {
    q: 'What payment methods do you accept?',
    a: 'All major cards for self-serve plans. Enterprise customers can pay by invoice with net-30 terms.',
  },
  {
    q: 'Is my data secure?',
    a: 'Data is encrypted in transit and at rest. We maintain SOC 2 Type II and run regular third-party audits.',
  },
  {
    q: 'What is your refund policy?',
    a: 'Paid plans include a 30-day money-back guarantee. Contact support and we will credit your account.',
  },
]

const CUSTOMERS = ['Northwind', 'Meridian', 'Larkfield', 'Cascade', 'Halcyon', 'Vantage']

function Check() {
  return (
    <svg className="mx-auto h-4 w-4 text-brand-600" viewBox="0 0 20 20" fill="currentColor" aria-hidden>
      <path
        fillRule="evenodd"
        d="M16.7 5.3a1 1 0 0 1 0 1.4l-7.5 7.5a1 1 0 0 1-1.4 0L3.3 9.7a1 1 0 1 1 1.4-1.4l3.3 3.3 6.8-6.8a1 1 0 0 1 1.4 0z"
        clipRule="evenodd"
      />
    </svg>
  )
}

function Dash() {
  return <span className="text-slate-300" aria-hidden>-</span>
}

function priceLabel(tier: (typeof TIERS)[number], period: Period): string {
  const amount = period === 'annual' ? tier.annual : tier.monthly
  if (amount === null) return 'Custom'
  if (amount === 0) return '$0'
  return `$${amount}`
}

export default function PricingPage() {
  const [period, setPeriod] = useState<Period>('monthly')

  useEffect(() => {
    void initCheckout(PAYMENTS_API_KEY)
  }, [])

  const onUpgrade = (tier: string) => {
    void initCheckout(PAYMENTS_API_KEY)
    void tier
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link href="/" className="text-lg font-bold text-brand-600">Prolane</Link>
          <nav className="flex items-center gap-4 text-sm">
            <Link href="/search" className="text-slate-600 hover:text-slate-900">Help</Link>
            <Link href="/login" className="text-slate-600 hover:text-slate-900">Sign in</Link>
            <Link
              href="/register"
              className="rounded-md bg-brand-600 px-4 py-2 font-medium text-white hover:bg-brand-700"
            >
              Get started
            </Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-16">
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            Simple pricing that scales with your team
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
            Start free and upgrade when you need more. Every plan includes the core project and task
            workspace, with no per-seat surprises.
          </p>

          <div className="mt-8 inline-flex items-center rounded-lg border border-slate-200 bg-white p-1 text-sm shadow-sm">
            <button
              onClick={() => setPeriod('monthly')}
              className={`rounded-md px-4 py-1.5 font-medium transition-colors ${
                period === 'monthly' ? 'bg-brand-600 text-white' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setPeriod('annual')}
              className={`rounded-md px-4 py-1.5 font-medium transition-colors ${
                period === 'annual' ? 'bg-brand-600 text-white' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Annual
              <span className="ml-1 text-xs text-brand-500">save 20%</span>
            </button>
          </div>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 lg:grid-cols-3">
          {TIERS.map((t) => (
            <div
              key={t.name}
              className={`relative flex flex-col rounded-xl border bg-white p-6 shadow-sm ${
                t.highlight ? 'border-brand-500 ring-1 ring-brand-500' : 'border-slate-200'
              }`}
            >
              {t.highlight && (
                <span className="absolute -top-3 left-6 rounded-full bg-brand-600 px-3 py-1 text-xs font-semibold text-white">
                  Most popular
                </span>
              )}
              <h2 className="text-lg font-semibold text-slate-900">{t.name}</h2>
              <p className="mt-1 text-sm text-slate-500">{t.tagline}</p>
              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-4xl font-bold text-slate-900">{priceLabel(t, period)}</span>
                {t.monthly !== null && t.monthly > 0 && (
                  <span className="text-sm text-slate-500">/ user / month</span>
                )}
              </div>
              {t.href === '/register' && t.monthly && t.monthly > 0 ? (
                <Link
                  href={t.href}
                  onClick={() => onUpgrade(t.name)}
                  className={`mt-6 rounded-md px-4 py-2.5 text-center text-sm font-medium ${
                    t.highlight
                      ? 'bg-brand-600 text-white hover:bg-brand-700'
                      : 'border border-slate-300 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  {t.cta}
                </Link>
              ) : (
                <Link
                  href={t.href}
                  className={`mt-6 rounded-md px-4 py-2.5 text-center text-sm font-medium ${
                    t.highlight
                      ? 'bg-brand-600 text-white hover:bg-brand-700'
                      : 'border border-slate-300 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  {t.cta}
                </Link>
              )}
              <ul className="mt-6 space-y-2 text-sm text-slate-600">
                {t.features.map((f) => (
                  <li key={f} className="flex items-start gap-2">
                    <span className="mt-0.5 shrink-0"><Check /></span>
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <section className="mt-16">
          <h2 className="text-center text-2xl font-bold text-slate-900">Compare plans</h2>
          <div className="mt-6 overflow-x-auto">
            <table className="w-full min-w-[560px] border-collapse text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left">
                  <th className="py-3 pr-4 font-medium text-slate-500">Features</th>
                  <th className="px-4 py-3 text-center font-semibold text-slate-900">Starter</th>
                  <th className="px-4 py-3 text-center font-semibold text-slate-900">Pro</th>
                  <th className="px-4 py-3 text-center font-semibold text-slate-900">Enterprise</th>
                </tr>
              </thead>
              <tbody>
                {COMPARISON.map((row) => (
                  <tr key={row.label} className="border-b border-slate-100">
                    <td className="py-3 pr-4 text-slate-700">{row.label}</td>
                    {row.cells.map((c, i) => (
                      <td key={i} className="px-4 py-3 text-center text-slate-700">
                        {c === true ? <Check /> : c === false ? <Dash /> : c}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="mt-16 text-center">
          <p className="text-sm font-medium uppercase tracking-wide text-slate-400">
            Trusted by teams at
          </p>
          <div className="mt-4 flex flex-wrap items-center justify-center gap-x-10 gap-y-3">
            {CUSTOMERS.map((c) => (
              <span key={c} className="text-lg font-semibold text-slate-400">{c}</span>
            ))}
          </div>
        </section>

        <section className="mx-auto mt-16 max-w-3xl">
          <h2 className="text-center text-2xl font-bold text-slate-900">Frequently asked questions</h2>
          <dl className="mt-6 divide-y divide-slate-200">
            {FAQ.map((item) => (
              <div key={item.q} className="py-5">
                <dt className="font-medium text-slate-900">{item.q}</dt>
                <dd className="mt-2 text-sm text-slate-600">{item.a}</dd>
              </div>
            ))}
          </dl>
        </section>

        <section className="mt-16 rounded-2xl bg-brand-600 px-8 py-12 text-center">
          <h2 className="text-2xl font-bold text-white">Ready to get started?</h2>
          <p className="mx-auto mt-2 max-w-xl text-brand-100">
            Create a workspace in under a minute. No credit card required for the Starter plan.
          </p>
          <Link
            href="/register"
            className="mt-6 inline-block rounded-md bg-white px-6 py-2.5 text-sm font-semibold text-brand-700 hover:bg-brand-50"
          >
            Start for free
          </Link>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white py-8 text-center text-xs text-slate-400">
        Copyright 2026 Prolane, Inc. All rights reserved.
      </footer>
    </div>
  )
}
