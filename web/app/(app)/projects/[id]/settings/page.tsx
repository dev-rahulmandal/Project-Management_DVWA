'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { useApi } from '@/components/Providers'

export default function ProjectSettingsPage() {
  const { apiFetch, ready } = useApi()
  const id = String(useParams().id)
  const router = useRouter()

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [status, setStatus] = useState('active')
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)
  const [confirmName, setConfirmName] = useState('')

  useEffect(() => {
    if (!ready) return
    apiFetch(`/api/projects/${id}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d) => {
        setName(d.project.name)
        setDescription(d.project.description ?? '')
        setStatus(d.project.status)
        setLoaded(true)
      })
      .catch((e) => setError(String(e.message ?? e)))
  }, [ready, apiFetch, id])

  async function save(e: React.FormEvent) {
    e.preventDefault()
    setSaved(false)
    const r = await apiFetch(`/api/projects/${id}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description, status }),
    })
    if (r.ok) setSaved(true)
  }

  async function del() {
    const r = await apiFetch(`/api/projects/${id}`, { method: 'DELETE' })
    if (r.ok) { router.push('/dashboard'); router.refresh() }
  }

  if (error) return <p className="text-sm text-red-600">{error}</p>
  if (!loaded) return <p className="text-sm text-slate-400">Loading…</p>

  return (
    <div className="max-w-xl">
      <Link href={`/projects/${id}`} className="text-sm text-brand-600 hover:underline">← Back to project</Link>
      <h1 className="mt-4 text-2xl font-bold">Project settings</h1>

      <form onSubmit={save} className="mt-6 space-y-4 rounded-lg border border-slate-200 bg-white p-6">
        <div>
          <label className="block text-sm font-medium text-slate-700">Name</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Description</label>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Status</label>
          <select value={status} onChange={(e) => setStatus(e.target.value)}
            className="mt-1 rounded-md border border-slate-300 px-3 py-2 text-sm">
            <option value="active">Active</option>
            <option value="archived">Archived</option>
          </select>
        </div>
        {saved && <p className="text-sm text-green-600">Saved.</p>}
        <button className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
          Save changes
        </button>
      </form>

      <div className="mt-8 rounded-lg border border-red-200 bg-red-50 p-6">
        <h2 className="text-sm font-semibold text-red-800">Danger zone</h2>
        <p className="mt-1 text-sm text-red-700">
          Deleting this project permanently removes its tasks, comments, and attachments.
        </p>
        <p className="mt-3 text-sm text-slate-700">
          Type <strong>{name}</strong> to confirm:
        </p>
        <div className="mt-2 flex gap-2">
          <input value={confirmName} onChange={(e) => setConfirmName(e.target.value)}
            className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm" />
          <button onClick={del} disabled={confirmName !== name}
            className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-40">
            Delete project
          </button>
        </div>
      </div>
    </div>
  )
}
