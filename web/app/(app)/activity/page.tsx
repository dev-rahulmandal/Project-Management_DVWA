'use client'

import { useCallback, useEffect, useState } from 'react'
import { useApi } from '@/components/Providers'

interface Item {
  action: string
  resourceType: string
  resourceId: number
  actor: string | null
  at: string
}

const PAGE = 25

function timeAgo(iso: string): string {
  const t = new Date(iso.replace(' ', 'T')).getTime()
  if (Number.isNaN(t)) return ''
  const s = Math.max(0, (Date.now() - t) / 1000)
  if (s < 3600) return `${Math.floor(s / 60)}m ago`
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`
  return `${Math.floor(s / 86400)}d ago`
}

export default function ActivityPage() {
  const { apiFetch, ready } = useApi()
  const [items, setItems] = useState<Item[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [resourceType, setResourceType] = useState('')
  const [error, setError] = useState('')

  const load = useCallback(() => {
    const qs = new URLSearchParams({ limit: String(PAGE), offset: String(page * PAGE) })
    if (resourceType) qs.set('resourceType', resourceType)
    apiFetch(`/api/activity?${qs}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d) => { setItems(d.activity); setTotal(d.total) })
      .catch((e) => setError(String(e.message ?? e)))
  }, [apiFetch, page, resourceType])

  useEffect(() => { if (ready) load() }, [ready, load])
  useEffect(() => { setPage(0) }, [resourceType])

  const pageCount = Math.max(1, Math.ceil(total / PAGE))
  const inputCls = 'rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500'

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Activity</h1>
          <p className="mt-1 text-slate-500">{total} events in your organization</p>
        </div>
        <select value={resourceType} onChange={(e) => setResourceType(e.target.value)} className={inputCls}>
          <option value="">All types</option>
          <option value="project">Projects</option>
          <option value="task">Tasks</option>
          <option value="user">Users</option>
          <option value="org">Organization</option>
        </select>
      </div>

      {error && <p className="mt-6 text-sm text-red-600">Failed to load: {error}</p>}

      <ul className="mt-6 divide-y divide-slate-100 overflow-hidden rounded-lg border border-slate-200 bg-white">
        {items.map((a, i) => (
          <li key={i} className="flex items-center justify-between px-5 py-3 text-sm">
            <span className="text-slate-700">
              <span className="font-medium">{a.actor ?? 'Someone'}</span>{' '}
              <span className="text-slate-500">{a.action.replace('.', ' ')}</span>{' '}
              <span className="text-slate-400">{a.resourceType} #{a.resourceId}</span>
            </span>
            <span className="shrink-0 text-xs text-slate-400">{timeAgo(a.at)}</span>
          </li>
        ))}
        {items.length === 0 && !error && <li className="px-5 py-4 text-sm text-slate-400">No activity.</li>}
      </ul>

      {pageCount > 1 && (
        <div className="mt-4 flex items-center justify-between text-sm">
          <button disabled={page === 0} onClick={() => setPage((p) => p - 1)}
            className="rounded-md border border-slate-300 px-3 py-1.5 font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-40">Previous</button>
          <span className="text-slate-500">Page {page + 1} of {pageCount}</span>
          <button disabled={page + 1 >= pageCount} onClick={() => setPage((p) => p + 1)}
            className="rounded-md border border-slate-300 px-3 py-1.5 font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-40">Next</button>
        </div>
      )}
    </div>
  )
}
