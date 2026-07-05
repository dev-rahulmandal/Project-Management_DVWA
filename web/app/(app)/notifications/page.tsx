'use client'

import { useCallback, useEffect, useState } from 'react'
import { useApi } from '@/components/Providers'

interface Notif {
  id: number
  kind: string
  title: string
  body: string | null
  link: string | null
  isRead: boolean
  createdAt: string
}

const KIND_ICON: Record<string, string> = {
  mention: '@', assignment: '◎', comment: '💬', system: '★',
}

function timeAgo(iso: string): string {
  const t = new Date(iso.replace(' ', 'T')).getTime()
  if (Number.isNaN(t)) return ''
  const s = Math.max(0, (Date.now() - t) / 1000)
  if (s < 3600) return `${Math.floor(s / 60)}m ago`
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`
  return `${Math.floor(s / 86400)}d ago`
}

export default function NotificationsPage() {
  const { apiFetch, ready } = useApi()
  const [items, setItems] = useState<Notif[] | null>(null)
  const [unread, setUnread] = useState(0)
  const [error, setError] = useState('')

  const load = useCallback(() => {
    apiFetch('/api/notifications?limit=100')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d) => { setItems(d.notifications); setUnread(d.unreadCount) })
      .catch((e) => setError(String(e.message ?? e)))
  }, [apiFetch])

  useEffect(() => { if (ready) load() }, [ready, load])

  async function markRead(n: Notif) {
    if (n.isRead) return
    setItems((prev) => prev?.map((x) => x.id === n.id ? { ...x, isRead: true } : x) ?? prev)
    setUnread((u) => Math.max(0, u - 1))
    await apiFetch(`/api/notifications/${n.id}/read`, { method: 'POST' })
  }

  async function markAll() {
    setItems((prev) => prev?.map((x) => ({ ...x, isRead: true })) ?? prev)
    setUnread(0)
    await apiFetch('/api/notifications/read-all', { method: 'POST' })
  }

  return (
    <div className="max-w-2xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Notifications</h1>
          <p className="mt-1 text-slate-500">{unread > 0 ? `${unread} unread` : 'All caught up'}</p>
        </div>
        {unread > 0 && (
          <button onClick={markAll} className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100">
            Mark all read
          </button>
        )}
      </div>

      {error && <p className="mt-6 text-sm text-red-600">Failed to load: {error}</p>}
      {!error && !items && <p className="mt-6 text-sm text-slate-400">Loading…</p>}
      {items && items.length === 0 && <p className="mt-6 text-sm text-slate-400">No notifications.</p>}

      {items && items.length > 0 && (
        <ul className="mt-6 divide-y divide-slate-100 overflow-hidden rounded-lg border border-slate-200 bg-white">
          {items.map((n) => (
            <li key={n.id} onClick={() => markRead(n)}
              className={`flex cursor-pointer items-start gap-3 px-5 py-3.5 transition hover:bg-slate-50 ${n.isRead ? '' : 'bg-brand-50/40'}`}>
              <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs text-slate-500">
                {KIND_ICON[n.kind] ?? '•'}
              </span>
              <div className="min-w-0 flex-1">
                <p className={`text-sm ${n.isRead ? 'text-slate-600' : 'font-medium text-slate-900'}`}>{n.title}</p>
                {n.body && <p className="mt-0.5 truncate text-xs text-slate-400">{n.body}</p>}
              </div>
              <div className="flex shrink-0 items-center gap-2">
                {!n.isRead && <span className="h-2 w-2 rounded-full bg-brand-500" />}
                <span className="text-xs text-slate-400">{timeAgo(n.createdAt)}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
