'use client'

import * as Popover from '@radix-ui/react-popover'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { useApi } from '@/components/Providers'
import { IconBell } from './icons'

interface Notif {
  id: number
  kind: string
  title: string
  body: string | null
  isRead: boolean
  createdAt: string
}

const KIND_ICON: Record<string, string> = { mention: '@', assignment: '◎', comment: '💬', system: '★' }

function timeAgo(iso: string): string {
  const t = new Date(iso.replace(' ', 'T')).getTime()
  if (Number.isNaN(t)) return ''
  const s = Math.max(0, (Date.now() - t) / 1000)
  if (s < 3600) return `${Math.floor(s / 60)}m`
  if (s < 86400) return `${Math.floor(s / 3600)}h`
  return `${Math.floor(s / 86400)}d`
}

/** Topbar notifications popover: unread badge (always), recent list (on open),
 *  mark-read and mark-all. Renders titles/bodies as escaped text. */
export function NotificationsMenu() {
  const { apiFetch, ready } = useApi()
  const [open, setOpen] = useState(false)
  const [items, setItems] = useState<Notif[] | null>(null)
  const [unread, setUnread] = useState(0)

  useEffect(() => {
    if (!ready) return
    apiFetch('/api/notifications?unreadOnly=true&limit=1')
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setUnread(d.unreadCount ?? 0))
      .catch(() => {})
  }, [ready, apiFetch])

  useEffect(() => {
    if (!open || !ready) return
    apiFetch('/api/notifications?limit=8')
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d) {
          setItems(d.notifications)
          setUnread(d.unreadCount ?? 0)
        }
      })
      .catch(() => {})
  }, [open, ready, apiFetch])

  async function markRead(n: Notif) {
    if (n.isRead) return
    setItems((prev) => prev?.map((x) => (x.id === n.id ? { ...x, isRead: true } : x)) ?? prev)
    setUnread((u) => Math.max(0, u - 1))
    await apiFetch(`/api/notifications/${n.id}/read`, { method: 'POST' })
  }

  async function markAll() {
    setItems((prev) => prev?.map((x) => ({ ...x, isRead: true })) ?? prev)
    setUnread(0)
    await apiFetch('/api/notifications/read-all', { method: 'POST' })
  }

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button
          aria-label="Notifications"
          className="relative grid h-8 w-8 place-items-center rounded-md text-slate-500 hover:bg-slate-100 hover:text-slate-800"
        >
          <IconBell size={18} />
          {unread > 0 && (
            <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-brand-600 px-1 text-[10px] font-bold text-white">
              {unread > 99 ? '99+' : unread}
            </span>
          )}
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          align="end"
          sideOffset={8}
          className="z-50 w-80 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg"
        >
          <div className="flex items-center justify-between border-b border-slate-100 px-4 py-2.5">
            <p className="text-sm font-semibold text-slate-900">Notifications</p>
            {unread > 0 && (
              <button onClick={markAll} className="text-xs font-medium text-brand-600 hover:underline">
                Mark all read
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto">
            {!items && <p className="px-4 py-6 text-center text-sm text-slate-400">Loading…</p>}
            {items && items.length === 0 && (
              <p className="px-4 py-6 text-center text-sm text-slate-400">No notifications.</p>
            )}
            {items?.map((n) => (
              <button
                key={n.id}
                onClick={() => markRead(n)}
                className={`flex w-full items-start gap-3 px-4 py-3 text-left transition hover:bg-slate-50 ${
                  n.isRead ? '' : 'bg-brand-50/40'
                }`}
              >
                <span className="mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full bg-slate-100 text-xs text-slate-500">
                  {KIND_ICON[n.kind] ?? '•'}
                </span>
                <span className="min-w-0 flex-1">
                  <span className={`block text-sm ${n.isRead ? 'text-slate-600' : 'font-medium text-slate-900'}`}>
                    {n.title}
                  </span>
                  {n.body && <span className="mt-0.5 block truncate text-xs text-slate-400">{n.body}</span>}
                </span>
                <span className="shrink-0 text-[10px] text-slate-400">{timeAgo(n.createdAt)}</span>
              </button>
            ))}
          </div>
          <Link
            href="/notifications"
            onClick={() => setOpen(false)}
            className="block border-t border-slate-100 px-4 py-2.5 text-center text-sm font-medium text-brand-600 hover:bg-slate-50"
          >
            View all
          </Link>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  )
}
