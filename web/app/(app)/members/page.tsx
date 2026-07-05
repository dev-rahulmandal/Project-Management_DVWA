'use client'

import { useEffect, useMemo, useState } from 'react'
import { useApi } from '@/components/Providers'

interface Member {
  id: number
  name: string
  email: string
  role: string
  isSuperAdmin: boolean
}

const ROLE_STYLE: Record<string, string> = {
  owner: 'bg-violet-50 text-violet-700',
  admin: 'bg-blue-50 text-blue-700',
  member: 'bg-slate-100 text-slate-600',
}

function initials(name: string): string {
  return name.split(/\s+/).map((w) => w[0]).slice(0, 2).join('').toUpperCase()
}

export default function MembersPage() {
  const { apiFetch, ready } = useApi()
  const [members, setMembers] = useState<Member[] | null>(null)
  const [error, setError] = useState('')
  const [q, setQ] = useState('')

  useEffect(() => {
    if (!ready) return
    apiFetch('/api/members')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d) => setMembers(d.members))
      .catch((e) => setError(String(e.message ?? e)))
  }, [ready, apiFetch])

  const filtered = useMemo(() => {
    if (!members) return []
    return members.filter((m) =>
      q === '' || m.name.toLowerCase().includes(q.toLowerCase()) || m.email.toLowerCase().includes(q.toLowerCase()))
  }, [members, q])

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Members</h1>
          <p className="mt-1 text-slate-500">{members ? `${filtered.length}` : '…'} people in your organization</p>
        </div>
      </div>

      <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search members…"
        className="mt-6 w-full max-w-sm rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" />

      {error && <p className="mt-6 text-sm text-red-600">Failed to load: {error}</p>}
      {!error && !members && <p className="mt-6 text-sm text-slate-400">Loading…</p>}

      {members && (
        <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((m) => (
            <div key={m.id} className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-4">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-100 text-sm font-semibold text-brand-700">
                {initials(m.name)}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-slate-800">{m.name}</p>
                <p className="truncate text-xs text-slate-400">{m.email}</p>
              </div>
              <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium capitalize ${ROLE_STYLE[m.role] ?? ROLE_STYLE.member}`}>
                {m.isSuperAdmin ? 'super' : m.role}
              </span>
            </div>
          ))}
          {filtered.length === 0 && <p className="text-sm text-slate-400">No members match.</p>}
        </div>
      )}
    </div>
  )
}
