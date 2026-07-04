'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useApi } from '@/components/Providers'

interface Overview {
  org: { id: number; name: string; planTier: string }
  counts: { members: number; projects: number; tasks: number }
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-1 text-3xl font-bold text-slate-900">{value}</p>
    </div>
  )
}

export default function AdminPage() {
  const { apiFetch, ready } = useApi()
  const [data, setData] = useState<Overview | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!ready) return
    // Admin-gated on the api (require_admin). Non-admins never reach this page
    // (server guard), and would get 403 here even if they did.
    apiFetch('/api/admin/overview')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d: Overview) => setData(d))
      .catch((e) => setError(String(e.message ?? e)))
  }, [ready, apiFetch])

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Admin</h1>
          <p className="mt-1 text-slate-500">Organization overview</p>
        </div>
        <div className="flex gap-2">
          <Link
            href="/admin/organization"
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Organization
          </Link>
          <Link
            href="/admin/members"
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            Manage members
          </Link>
        </div>
      </div>

      {error && <p className="mt-6 text-sm text-red-600">Failed to load: {error}</p>}
      {!error && !data && <p className="mt-6 text-sm text-slate-400">Loading…</p>}

      {data && (
        <>
          <div className="mt-6 flex items-center gap-3">
            <span className="text-lg font-semibold text-slate-900">{data.org.name}</span>
            <span className="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-medium capitalize text-brand-700">
              {data.org.planTier}
            </span>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard label="Members" value={data.counts.members} />
            <StatCard label="Projects" value={data.counts.projects} />
            <StatCard label="Tasks" value={data.counts.tasks} />
          </div>
        </>
      )}
    </div>
  )
}
