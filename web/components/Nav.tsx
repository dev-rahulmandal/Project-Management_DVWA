'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { useApi } from '@/components/Providers'

export function Nav({ email, role, isAdmin }: { email: string; role: string; isAdmin: boolean }) {
  const router = useRouter()
  const { apiFetch, ready } = useApi()
  const [unread, setUnread] = useState(0)

  useEffect(() => {
    if (!ready) return
    apiFetch('/api/notifications?unreadOnly=true&limit=1')
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setUnread(d.unreadCount ?? 0))
      .catch(() => {})
  }, [ready, apiFetch])

  async function logout() {
    await fetch('/api/auth/logout', { method: 'POST' })
    router.push('/login')
    router.refresh()
  }

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3">
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="text-lg font-bold text-brand-600">
            Prolane
          </Link>
          <nav className="flex items-center gap-4 text-sm font-medium text-slate-600">
            <Link href="/dashboard" className="hover:text-slate-900">Dashboard</Link>
            <Link href="/projects" className="hover:text-slate-900">Projects</Link>
            <Link href="/tasks" className="hover:text-slate-900">Tasks</Link>
            <Link href="/members" className="hover:text-slate-900">Members</Link>
            <Link href="/billing" className="hover:text-slate-900">Billing</Link>
            {isAdmin && <Link href="/admin" className="hover:text-slate-900">Admin</Link>}
            <Link href="/developer" className="hover:text-slate-900">Developer</Link>
            <Link href="/settings" className="hover:text-slate-900">Settings</Link>
          </nav>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <Link href="/notifications" className="relative text-slate-400 hover:text-slate-700" title="Notifications" aria-label="Notifications">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            {unread > 0 && (
              <span className="absolute -right-2 -top-2 flex h-4 min-w-4 items-center justify-center rounded-full bg-brand-600 px-1 text-[10px] font-bold text-white">
                {unread > 99 ? '99+' : unread}
              </span>
            )}
          </Link>
          <span className="text-slate-500">{email}</span>
          <span className="rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700">{role}</span>
          <button onClick={logout} className="rounded-md border border-slate-300 px-3 py-1 font-medium text-slate-700 hover:bg-slate-100">
            Sign out
          </button>
        </div>
      </div>
    </header>
  )
}
