'use client'

import { useEffect, useState } from 'react'
import { useApi } from '@/components/Providers'

interface Member {
  id: number
  email: string
  fullName: string
  role: string
}

function initials(name: string) {
  return name
    .split(/\s+/)
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

function RoleBadge({ role }: { role: string }) {
  const styles =
    role === 'owner'
      ? 'bg-brand-50 text-brand-700'
      : role === 'admin'
        ? 'bg-amber-50 text-amber-700'
        : 'bg-slate-100 text-slate-500'
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${styles}`}>
      {role}
    </span>
  )
}

export default function TeamPage() {
  const { apiFetch, ready } = useApi()
  const [members, setMembers] = useState<Member[] | null>(null)
  const [error, setError] = useState('')

  // org-scoped: GET /api/users returns only the caller's org members.
  useEffect(() => {
    if (!ready) return
    apiFetch('/api/users')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d) => setMembers(d.users))
      .catch((e) => setError(String(e.message ?? e)))
  }, [ready, apiFetch])

  return (
    <div>
      <h1 className="text-2xl font-bold">Team</h1>
      <p className="mt-1 text-slate-500">People in your organization</p>

      {error && <p className="mt-6 text-sm text-red-600">Failed to load: {error}</p>}
      {!error && !members && <p className="mt-6 text-sm text-slate-400">Loading…</p>}

      {members && members.length > 0 && (
        <ul className="mt-6 divide-y divide-slate-200 overflow-hidden rounded-lg border border-slate-200 bg-white">
          {members.map((m) => (
            <li key={m.id} className="flex items-center justify-between px-5 py-4">
              <div className="flex items-center gap-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
                  {initials(m.fullName)}
                </span>
                <div>
                  <p className="font-medium text-slate-900">{m.fullName}</p>
                  <p className="text-sm text-slate-500">{m.email}</p>
                </div>
              </div>
              <RoleBadge role={m.role} />
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
