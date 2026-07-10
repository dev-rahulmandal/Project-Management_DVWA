'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { useApi } from '@/components/Providers'

interface Project {
  id: number
  orgId: number
  name: string
  description: string | null
  status: string
}

const PAGE_SIZE = 12

function StatusBadge({ status }: { status: string }) {
  const styles = status === 'active' ? 'bg-green-50 text-green-700' : 'bg-slate-100 text-slate-500'
  return <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${styles}`}>{status}</span>
}

export default function ProjectsPage() {
  const { apiFetch, ready } = useApi()
  const [projects, setProjects] = useState<Project[] | null>(null)
  const [error, setError] = useState('')

  const [q, setQ] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sort, setSort] = useState<'name' | 'recent'>('recent')
  const [page, setPage] = useState(1)
  const [view, setView] = useState<'active' | 'trash'>('active')

  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')

  const load = useCallback(() => {
    apiFetch(`/api/projects${view === 'trash' ? '?trashed=true' : ''}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d) => setProjects(d.projects))
      .catch((e) => setError(String(e.message ?? e)))
  }, [apiFetch, view])

  useEffect(() => {
    if (ready) load()
  }, [ready, load])

  async function trash(id: number) {
    await apiFetch(`/api/projects/${id}/trash`, { method: 'POST' })
    load()
  }
  async function restore(id: number) {
    await apiFetch(`/api/projects/${id}/restore`, { method: 'POST' })
    load()
  }

  const filtered = useMemo(() => {
    if (!projects) return []
    let list = projects.filter((p) =>
      (statusFilter === 'all' || p.status === statusFilter) &&
      (q === '' || p.name.toLowerCase().includes(q.toLowerCase()) ||
        (p.description ?? '').toLowerCase().includes(q.toLowerCase())))
    list = sort === 'name'
      ? [...list].sort((a, b) => a.name.localeCompare(b.name))
      : [...list].sort((a, b) => b.id - a.id)
    return list
  }, [projects, q, statusFilter, sort])

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const shown = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
  useEffect(() => { setPage(1) }, [q, statusFilter, sort, view])

  async function createProject(e: React.FormEvent) {
    e.preventDefault()
    setCreating(true)
    setCreateError('')
    try {
      const r = await apiFetch('/api/projects', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description: description || null }),
      })
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      setName(''); setDescription(''); setShowForm(false); load()
    } catch (err) {
      setCreateError(String((err as Error).message ?? err))
    } finally {
      setCreating(false)
    }
  }

  const inputCls = 'rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500'

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Projects</h1>
          <p className="mt-1 text-slate-500">{projects ? `${filtered.length} of ${projects.length}` : '…'} projects</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setView((v) => (v === 'active' ? 'trash' : 'active'))}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100">
            {view === 'active' ? 'Trash' : '← Projects'}
          </button>
          {view === 'active' && (
            <button onClick={() => setShowForm((v) => !v)} className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
              {showForm ? 'Cancel' : 'New project'}
            </button>
          )}
        </div>
      </div>

      {showForm && (
        <form onSubmit={createProject} className="mt-6 space-y-4 rounded-lg border border-slate-200 bg-white p-6">
          <input value={name} onChange={(e) => setName(e.target.value)} required placeholder="Project name" className={`w-full ${inputCls}`} />
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} placeholder="Description (optional)" className={`w-full ${inputCls}`} />
          {createError && <p className="text-sm text-red-600">Could not create: {createError}</p>}
          <button type="submit" disabled={creating} className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50">
            {creating ? 'Creating…' : 'Create project'}
          </button>
        </form>
      )}

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search projects…" className={`${inputCls} flex-1 min-w-[180px]`} />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className={inputCls}>
          <option value="all">All statuses</option>
          <option value="active">Active</option>
          <option value="archived">Archived</option>
        </select>
        <select value={sort} onChange={(e) => setSort(e.target.value as 'name' | 'recent')} className={inputCls}>
          <option value="recent">Newest</option>
          <option value="name">Name A–Z</option>
        </select>
      </div>

      {error && <p className="mt-6 text-sm text-red-600">Failed to load: {error}</p>}
      {!error && !projects && <p className="mt-6 text-sm text-slate-400">Loading…</p>}
      {projects && shown.length === 0 && <p className="mt-6 text-sm text-slate-400">No projects match.</p>}

      {shown.length > 0 && (
        <ul className="mt-4 divide-y divide-slate-200 overflow-hidden rounded-lg border border-slate-200 bg-white">
          {shown.map((p) => (
            <li key={p.id} className="flex items-center gap-3 px-5 py-4 transition hover:bg-slate-50">
              <Link href={`/projects/${p.id}`} className="min-w-0 flex-1">
                <p className="font-medium text-slate-900">{p.name}</p>
                {p.description && <p className="mt-0.5 truncate text-sm text-slate-500">{p.description}</p>}
              </Link>
              <StatusBadge status={p.status} />
              {view === 'active' ? (
                <button onClick={() => trash(p.id)} className="shrink-0 text-xs font-medium text-slate-400 hover:text-red-600">Trash</button>
              ) : (
                <button onClick={() => restore(p.id)} className="shrink-0 text-xs font-medium text-brand-600 hover:underline">Restore</button>
              )}
            </li>
          ))}
        </ul>
      )}

      {pageCount > 1 && (
        <div className="mt-4 flex items-center justify-between text-sm">
          <button disabled={page === 1} onClick={() => setPage((p) => p - 1)}
            className="rounded-md border border-slate-300 px-3 py-1.5 font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-40">Previous</button>
          <span className="text-slate-500">Page {page} of {pageCount}</span>
          <button disabled={page === pageCount} onClick={() => setPage((p) => p + 1)}
            className="rounded-md border border-slate-300 px-3 py-1.5 font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-40">Next</button>
        </div>
      )}
    </div>
  )
}
