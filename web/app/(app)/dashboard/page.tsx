'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useApi } from '@/components/Providers'

interface Dash {
  projects: { total: number; active: number; archived: number }
  tasks: {
    total: number
    byStatus: Record<string, number>
    byPriority: Record<string, number>
    overdue: number
    dueSoon: number
    completionRate: number
  }
  members: number
  unreadNotifications: number
  activityByDay: { date: string; count: number }[]
  recentActivity: { action: string; resourceType: string; resourceId: number; at: string; actor: string | null }[]
}

const STATUS_COLORS: Record<string, string> = {
  open: '#94a3b8', in_progress: '#6366f1', done: '#22c55e',
}
const STATUS_LABEL: Record<string, string> = {
  open: 'Open', in_progress: 'In progress', done: 'Done',
}

function Stat({ label, value, accent }: { label: string; value: string | number; accent?: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`mt-1 text-3xl font-bold ${accent ?? 'text-slate-900'}`}>{value}</p>
    </div>
  )
}

function Sparkline({ data }: { data: { date: string; count: number }[] }) {
  if (data.length === 0) return <p className="text-sm text-slate-400">No activity yet.</p>
  const w = 520, h = 120, pad = 6
  const max = Math.max(...data.map((d) => d.count), 1)
  const step = data.length > 1 ? (w - pad * 2) / (data.length - 1) : 0
  const pts = data.map((d, i) => [pad + i * step, h - pad - (d.count / max) * (h - pad * 2)])
  const line = pts.map((p) => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ')
  const area = `${pad},${h - pad} ${line} ${(pad + (data.length - 1) * step).toFixed(1)},${h - pad}`
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full" preserveAspectRatio="none" style={{ height: 120 }}>
      <polygon points={area} fill="#6366f1" opacity="0.10" />
      <polyline points={line} fill="none" stroke="#6366f1" strokeWidth="2" />
      {pts.map((p, i) => <circle key={i} cx={p[0]} cy={p[1]} r="2" fill="#6366f1" />)}
    </svg>
  )
}

function timeAgo(iso: string): string {
  const t = new Date(iso.replace(' ', 'T')).getTime()
  if (Number.isNaN(t)) return ''
  const s = Math.max(0, (Date.now() - t) / 1000)
  if (s < 3600) return `${Math.floor(s / 60)}m ago`
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`
  return `${Math.floor(s / 86400)}d ago`
}

export default function DashboardPage() {
  const { apiFetch, ready } = useApi()
  const [d, setD] = useState<Dash | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!ready) return
    apiFetch('/api/dashboard')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(setD)
      .catch((e) => setError(String(e.message ?? e)))
  }, [ready, apiFetch])

  if (error) return <p className="text-sm text-red-600">Failed to load dashboard: {error}</p>
  if (!d) return <p className="text-sm text-slate-400">Loading…</p>

  const statusMax = Math.max(...Object.values(d.tasks.byStatus), 1)

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Overview</h1>
          <p className="mt-1 text-slate-500">Your organization at a glance</p>
        </div>
        <Link href="/projects" className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
          View projects
        </Link>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <Stat label="Projects" value={d.projects.total} />
        <Stat label="Tasks" value={d.tasks.total} />
        <Stat label="Members" value={d.members} />
        <Stat label="Complete" value={`${d.tasks.completionRate}%`} accent="text-green-600" />
        <Stat label="Overdue" value={d.tasks.overdue} accent={d.tasks.overdue ? 'text-red-600' : 'text-slate-900'} />
        <Stat label="Due soon" value={d.tasks.dueSoon} accent={d.tasks.dueSoon ? 'text-amber-600' : 'text-slate-900'} />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-white p-5 lg:col-span-2">
          <h2 className="text-sm font-semibold text-slate-700">Activity · last 14 days</h2>
          <div className="mt-3"><Sparkline data={d.activityByDay} /></div>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-5">
          <h2 className="text-sm font-semibold text-slate-700">Tasks by status</h2>
          <div className="mt-4 space-y-3">
            {['open', 'in_progress', 'done'].map((s) => {
              const n = d.tasks.byStatus[s] ?? 0
              return (
                <div key={s}>
                  <div className="flex justify-between text-xs text-slate-500">
                    <span>{STATUS_LABEL[s]}</span><span>{n}</span>
                  </div>
                  <div className="mt-1 h-2 overflow-hidden rounded-full bg-slate-100">
                    <div className="h-full rounded-full" style={{ width: `${(n / statusMax) * 100}%`, background: STATUS_COLORS[s] }} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      <div className="mt-6 rounded-lg border border-slate-200 bg-white">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
          <h2 className="text-sm font-semibold text-slate-700">Recent activity</h2>
          <Link href="/activity" className="text-xs font-medium text-brand-600 hover:underline">View all →</Link>
        </div>
        {d.recentActivity.length === 0 ? (
          <p className="px-5 py-4 text-sm text-slate-400">Nothing yet.</p>
        ) : (
          <ul className="divide-y divide-slate-50">
            {d.recentActivity.map((a, i) => (
              <li key={i} className="flex items-center justify-between px-5 py-3 text-sm">
                <span className="text-slate-700">
                  <span className="font-medium">{a.actor ?? 'Someone'}</span>{' '}
                  <span className="text-slate-500">{a.action.replace('.', ' ')}</span>{' '}
                  <span className="text-slate-400">{a.resourceType} #{a.resourceId}</span>
                </span>
                <span className="shrink-0 text-xs text-slate-400">{timeAgo(a.at)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
