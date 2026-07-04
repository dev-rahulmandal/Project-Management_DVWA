'use client'

import { useEffect, useState } from 'react'
import { useApi } from '@/components/Providers'

interface Me {
  id: number
  email: string
  fullName: string
  role: string
  orgId: number
  isSuperAdmin: boolean
}

export default function SettingsPage() {
  const { apiFetch, ready } = useApi()
  const [me, setMe] = useState<Me | null>(null)
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [loadError, setLoadError] = useState('')
  const [saving, setSaving] = useState(false)
  const [status, setStatus] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null)

  const [curPw, setCurPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [pwSaving, setPwSaving] = useState(false)
  const [pwStatus, setPwStatus] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null)

  useEffect(() => {
    if (!ready) return
    apiFetch('/api/me')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d: Me) => {
        setMe(d)
        setFullName(d.fullName)
        setEmail(d.email)
      })
      .catch((e) => setLoadError(String(e.message ?? e)))
  }, [ready, apiFetch])

  async function save(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setStatus(null)
    try {
      // Profile edit - submits the caller-editable fields to PATCH /api/me.
      const r = await apiFetch('/api/me', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fullName, email }),
      })
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const updated: Me = await r.json()
      setMe(updated)
      setFullName(updated.fullName)
      setEmail(updated.email)
      setStatus({ kind: 'ok', text: 'Profile updated.' })
    } catch (err) {
      setStatus({ kind: 'err', text: `Could not save: ${String((err as Error).message ?? err)}` })
    } finally {
      setSaving(false)
    }
  }

  async function changePassword(e: React.FormEvent) {
    e.preventDefault()
    setPwSaving(true)
    setPwStatus(null)
    try {
      const r = await apiFetch('/api/me/password', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ currentPassword: curPw, newPassword: newPw }),
      })
      if (r.ok) {
        setPwStatus({ kind: 'ok', text: 'Password changed.' })
        setCurPw(''); setNewPw('')
      } else {
        const d = await r.json().catch(() => ({}))
        setPwStatus({ kind: 'err', text:
          d.detail === 'wrong_current_password' ? 'Current password is incorrect.'
          : d.detail === 'weak_password' ? 'New password must be at least 8 characters.'
          : 'Could not change password.' })
      }
    } finally {
      setPwSaving(false)
    }
  }

  return (
    <div className="max-w-xl">
      <h1 className="text-2xl font-bold">Settings</h1>
      <p className="mt-1 text-slate-500">Manage your account profile</p>

      {loadError && (
        <p className="mt-6 text-sm text-red-600">Failed to load profile: {loadError}</p>
      )}
      {!loadError && !me && <p className="mt-6 text-sm text-slate-400">Loading…</p>}

      {me && (
        <form onSubmit={save} className="mt-6 space-y-5 rounded-lg border border-slate-200 bg-white p-6">
          <div>
            <label htmlFor="fullName" className="block text-sm font-medium text-slate-700">
              Full name
            </label>
            <input
              id="fullName"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-slate-700">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>

          {/* Read-only account facts - role/org are managed by your administrator. */}
          <div className="grid grid-cols-2 gap-4 border-t border-slate-100 pt-4 text-sm">
            <div>
              <span className="block text-xs uppercase tracking-wide text-slate-400">Role</span>
              <span className="mt-0.5 block font-medium capitalize text-slate-700">{me.role}</span>
            </div>
            <div>
              <span className="block text-xs uppercase tracking-wide text-slate-400">Organization</span>
              <span className="mt-0.5 block font-medium text-slate-700">#{me.orgId}</span>
            </div>
          </div>

          {status && (
            <p className={`text-sm ${status.kind === 'ok' ? 'text-green-600' : 'text-red-600'}`}>
              {status.text}
            </p>
          )}

          <button
            type="submit"
            disabled={saving}
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {saving ? 'Saving…' : 'Save changes'}
          </button>
        </form>
      )}

      {me && (
        <form onSubmit={changePassword} className="mt-8 space-y-4 rounded-lg border border-slate-200 bg-white p-6">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Change password</h2>
          <div>
            <label className="block text-sm font-medium text-slate-700">Current password</label>
            <input type="password" value={curPw} onChange={(e) => setCurPw(e.target.value)} required
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">New password</label>
            <input type="password" value={newPw} onChange={(e) => setNewPw(e.target.value)} required minLength={8}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500" />
          </div>
          {pwStatus && (
            <p className={`text-sm ${pwStatus.kind === 'ok' ? 'text-green-600' : 'text-red-600'}`}>{pwStatus.text}</p>
          )}
          <button type="submit" disabled={pwSaving}
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50">
            {pwSaving ? 'Updating…' : 'Update password'}
          </button>
        </form>
      )}
    </div>
  )
}
