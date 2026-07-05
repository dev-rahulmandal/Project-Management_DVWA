'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { useApi } from '@/components/Providers'

interface Label { id: number; name: string; color: string }
interface Task {
  id: number
  projectId: number
  projectName: string
  title: string
  status: string
  priority: string
  assigneeId: number | null
  assigneeName: string | null
  dueDate: string | null
  labels: Label[]
}

const COLUMNS = [
  { key: 'open', label: 'Open' },
  { key: 'in_progress', label: 'In progress' },
  { key: 'done', label: 'Done' },
]
const NEXT: Record<string, string> = { open: 'in_progress', in_progress: 'done', done: 'open' }
const PRIO_COLOR: Record<string, string> = { low: 'bg-slate-100 text-slate-500', medium: 'bg-blue-50 text-blue-600', high: 'bg-red-50 text-red-600' }
const LABEL_COLOR: Record<string, string> = {
  red: 'bg-red-50 text-red-700', green: 'bg-green-50 text-green-700', slate: 'bg-slate-100 text-slate-600',
  amber: 'bg-amber-50 text-amber-700', blue: 'bg-blue-50 text-blue-700', violet: 'bg-violet-50 text-violet-700',
  pink: 'bg-pink-50 text-pink-700', cyan: 'bg-cyan-50 text-cyan-700', orange: 'bg-orange-50 text-orange-700', teal: 'bg-teal-50 text-teal-700',
}

export default function TasksBoardPage() {
  const { apiFetch, ready } = useApi()
  const [tasks, setTasks] = useState<Task[] | null>(null)
  const [labels, setLabels] = useState<Label[]>([])
  const [error, setError] = useState('')

  const [q, setQ] = useState('')
  const [priority, setPriority] = useState('')
  const [labelId, setLabelId] = useState('')

  const load = useCallback(() => {
    apiFetch('/api/tasks?limit=1000')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d) => setTasks(d.tasks))
      .catch((e) => setError(String(e.message ?? e)))
    apiFetch('/api/labels').then((r) => r.ok ? r.json() : { labels: [] }).then((d) => setLabels(d.labels ?? []))
  }, [apiFetch])

  useEffect(() => { if (ready) load() }, [ready, load])

  const filtered = useMemo(() => {
    if (!tasks) return []
    return tasks.filter((t) =>
      (priority === '' || t.priority === priority) &&
      (labelId === '' || t.labels.some((l) => String(l.id) === labelId)) &&
      (q === '' || t.title.toLowerCase().includes(q.toLowerCase()) || t.projectName.toLowerCase().includes(q.toLowerCase())))
  }, [tasks, q, priority, labelId])

  const byStatus = (s: string) => filtered.filter((t) => t.status === s)

  async function move(t: Task) {
    const next = NEXT[t.status]
    setTasks((prev) => prev?.map((x) => x.id === t.id ? { ...x, status: next } : x) ?? prev)
    await apiFetch(`/api/tasks/${t.id}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status: next }),
    })
  }

  async function exportTasks(format: 'csv' | 'json') {
    const r = await apiFetch(`/api/export/tasks?format=${format}`)
    const blob = await r.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `tasks.${format}`
    a.click()
    URL.revokeObjectURL(url)
  }

  const inputCls = 'rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500'

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Tasks</h1>
          <p className="mt-1 text-slate-500">{tasks ? `${filtered.length} tasks` : '…'} across your projects</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => exportTasks('csv')} className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100">Export CSV</button>
          <button onClick={() => exportTasks('json')} className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100">JSON</button>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search tasks…" className={`${inputCls} flex-1 min-w-[180px]`} />
        <select value={priority} onChange={(e) => setPriority(e.target.value)} className={inputCls}>
          <option value="">All priorities</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option>
        </select>
        <select value={labelId} onChange={(e) => setLabelId(e.target.value)} className={inputCls}>
          <option value="">All labels</option>
          {labels.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
        </select>
      </div>

      {error && <p className="mt-6 text-sm text-red-600">Failed to load: {error}</p>}
      {!error && !tasks && <p className="mt-6 text-sm text-slate-400">Loading…</p>}

      {tasks && (
        <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
          {COLUMNS.map((col) => {
            const items = byStatus(col.key)
            return (
              <div key={col.key} className="rounded-lg bg-slate-50 p-3">
                <div className="flex items-center justify-between px-1 pb-2">
                  <h2 className="text-sm font-semibold text-slate-700">{col.label}</h2>
                  <span className="rounded-full bg-white px-2 py-0.5 text-xs font-medium text-slate-500">{items.length}</span>
                </div>
                <div className="space-y-2">
                  {items.slice(0, 60).map((t) => (
                    <div key={t.id} className="rounded-md border border-slate-200 bg-white p-3 shadow-sm">
                      <div className="flex items-start justify-between gap-2">
                        <Link href={`/tasks/${t.id}`} className="text-sm font-medium text-slate-800 hover:text-brand-600">{t.title}</Link>
                        <button onClick={() => move(t)} title="Move to next column"
                          className="shrink-0 rounded border border-slate-200 px-1.5 text-xs text-slate-400 hover:bg-slate-50">→</button>
                      </div>
                      <p className="mt-1 text-xs text-slate-400">{t.projectName}</p>
                      <div className="mt-2 flex flex-wrap items-center gap-1.5">
                        <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium capitalize ${PRIO_COLOR[t.priority] ?? ''}`}>{t.priority}</span>
                        {t.labels.map((l) => (
                          <span key={l.id} className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${LABEL_COLOR[l.color] ?? 'bg-slate-100 text-slate-600'}`}>{l.name}</span>
                        ))}
                        {t.assigneeName && <span className="ml-auto text-[10px] text-slate-400">{t.assigneeName}</span>}
                      </div>
                    </div>
                  ))}
                  {items.length > 60 && <p className="px-1 text-xs text-slate-400">+{items.length - 60} more…</p>}
                  {items.length === 0 && <p className="px-1 py-4 text-center text-xs text-slate-300">Nothing here</p>}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
