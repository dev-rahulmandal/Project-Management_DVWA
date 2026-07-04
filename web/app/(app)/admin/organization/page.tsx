'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useApi } from '@/components/Providers'

export default function OrgSettingsPage() {
  const { apiFetch, ready } = useApi()
  const router = useRouter()

  const [name, setName] = useState('')
  const [plan, setPlan] = useState('starter')
  const [slug, setSlug] = useState('')
  const [isOwner, setIsOwner] = useState(false)
  const [loaded, setLoaded] = useState(false)
  const [saved, setSaved] = useState(false)
  const [confirm, setConfirm] = useState('')

  useEffect(() => {
    if (!ready) return
    Promise.all([apiFetch('/api/org'), apiFetch('/api/me')]).then(async ([o, m]) => {
      if (o.ok) { const d = await o.json(); setName(d.org.name); setPlan(d.org.planTier); setSlug(d.org.slug) }
      if (m.ok) { const me = await m.json(); setIsOwner(me.isSuperAdmin || me.role === 'owner') }
      setLoaded(true)
    })
  }, [ready, apiFetch])

  async function save(e: React.FormEvent) {
    e.preventDefault()
    setSaved(false)
    const r = await apiFetch('/api/org', {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, planTier: plan }),
    })
    if (r.ok) setSaved(true)
  }

  async function deleteOrg() {
    const r = await apiFetch('/api/org', { method: 'DELETE' })
    if (r.ok) { await fetch('/api/auth/logout', { method: 'POST' }); router.push('/login') }
  }

  if (!loaded) return <p className="text-sm text-slate-400">Loading…</p>

  return (
    <div className="max-w-xl">
      <Link href="/admin" className="text-sm text-brand-600 hover:underline">← Admin</Link>
      <h1 className="mt-4 text-2xl font-bold">Organization settings</h1>

      <form onSubmit={save} className="mt-6 space-y-4 rounded-lg border border-slate-200 bg-white p-6">
        <div>
          <label className="block text-sm font-medium text-slate-700">Organization name</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700">Plan</label>
          <select value={plan} onChange={(e) => setPlan(e.target.value)}
            className="mt-1 rounded-md border border-slate-300 px-3 py-2 text-sm">
            <option value="starter">Starter</option>
            <option value="pro">Pro</option>
            <option value="enterprise">Enterprise</option>
          </select>
        </div>
        <p className="text-xs text-slate-400">Slug: {slug}</p>
        {saved && <p className="text-sm text-green-600">Saved.</p>}
        <button className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
          Save changes
        </button>
      </form>

      {isOwner && (
        <div className="mt-8 rounded-lg border border-red-200 bg-red-50 p-6">
          <h2 className="text-sm font-semibold text-red-800">Danger zone</h2>
          <p className="mt-1 text-sm text-red-700">
            Deleting the organization permanently removes every member, project, task, and file. This cannot be undone.
          </p>
          <p className="mt-3 text-sm text-slate-700">Type the slug <strong>{slug}</strong> to confirm:</p>
          <div className="mt-2 flex gap-2">
            <input value={confirm} onChange={(e) => setConfirm(e.target.value)}
              className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm" />
            <button onClick={deleteOrg} disabled={confirm !== slug}
              className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-40">
              Delete organization
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
