'use client'

import { useCallback, useEffect, useState } from 'react'
import { useApi } from '@/components/Providers'

// Mirrors api ALLOWED_SCOPES (api/routes/keys.py) and webhook KNOWN_EVENTS.
const SCOPES = ['projects:read', 'projects:write', 'tasks:read', 'tasks:write', 'profile:read']
const EVENTS = ['order.paid', 'task.created', 'member.invited']

interface Pat { id: number; name: string; prefix: string; scopes: string[]; createdAt: string }
interface Hook { id: number; url: string; events: string[]; active: boolean; secret: string }

export default function DeveloperPage() {
  const { apiFetch, ready } = useApi()

  // ---- Personal access tokens ----
  const [keys, setKeys] = useState<Pat[]>([])
  const [keyName, setKeyName] = useState('')
  const [keyScopes, setKeyScopes] = useState<string[]>(['projects:read'])
  const [newToken, setNewToken] = useState<string | null>(null)
  const [keyErr, setKeyErr] = useState('')

  // ---- Webhooks ----
  const [hooks, setHooks] = useState<Hook[]>([])
  const [hookUrl, setHookUrl] = useState('')
  const [hookEvents, setHookEvents] = useState<string[]>([])
  const [newSecret, setNewSecret] = useState<string | null>(null)
  const [hookErr, setHookErr] = useState('')
  const [testResult, setTestResult] = useState<Record<number, string>>({})

  const loadKeys = useCallback(() => {
    apiFetch('/api/keys')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d) => setKeys(d.keys))
      .catch((e) => setKeyErr(String(e.message ?? e)))
  }, [apiFetch])

  const loadHooks = useCallback(() => {
    apiFetch('/api/webhooks')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d) => setHooks(d.webhooks))
      .catch((e) => setHookErr(String(e.message ?? e)))
  }, [apiFetch])

  useEffect(() => {
    if (!ready) return
    loadKeys()
    loadHooks()
  }, [ready, loadKeys, loadHooks])

  function toggle(list: string[], set: (v: string[]) => void, value: string) {
    set(list.includes(value) ? list.filter((s) => s !== value) : [...list, value])
  }

  async function createKey(e: React.FormEvent) {
    e.preventDefault()
    setKeyErr('')
    setNewToken(null)
    try {
      const r = await apiFetch('/api/keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: keyName || 'token', scopes: keyScopes }),
      })
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const d = await r.json()
      setNewToken(d.token) // shown exactly once
      setKeyName('')
      loadKeys()
    } catch (err) {
      setKeyErr(String((err as Error).message ?? err))
    }
  }

  async function revokeKey(id: number) {
    await apiFetch(`/api/keys/${id}`, { method: 'DELETE' })
    loadKeys()
  }

  async function createHook(e: React.FormEvent) {
    e.preventDefault()
    setHookErr('')
    setNewSecret(null)
    try {
      const r = await apiFetch('/api/webhooks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: hookUrl, events: hookEvents }),
      })
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      const d = await r.json()
      setNewSecret(d.secret) // shown exactly once
      setHookUrl('')
      setHookEvents([])
      loadHooks()
    } catch (err) {
      setHookErr(String((err as Error).message ?? err))
    }
  }

  async function testHook(id: number) {
    setTestResult((p) => ({ ...p, [id]: 'Sending…' }))
    const r = await apiFetch(`/api/webhooks/${id}/test`, { method: 'POST' })
    const d = await r.json().catch(() => ({}))
    setTestResult((p) => ({
      ...p,
      [id]: r.ok ? `Delivered → HTTP ${d.status}` : `Failed → ${d.detail ?? r.status}`,
    }))
  }

  async function deleteHook(id: number) {
    await apiFetch(`/api/webhooks/${id}`, { method: 'DELETE' })
    loadHooks()
  }

  const inputCls =
    'mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500'
  const btnCls =
    'rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50'

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold">Developer</h1>
      <p className="mt-1 text-slate-500">Personal access tokens and webhooks for integrating with the API.</p>

      {/* ---------------- Personal access tokens ---------------- */}
      <section className="mt-8">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Personal access tokens</h2>

        {newToken && (
          <div className="mt-3 rounded-lg border border-amber-300 bg-amber-50 p-4">
            <p className="text-sm font-medium text-amber-800">
              Copy your token now - it will not be shown again.
            </p>
            <code className="mt-2 block break-all rounded bg-white px-3 py-2 font-mono text-sm text-slate-800">
              {newToken}
            </code>
          </div>
        )}

        <form onSubmit={createKey} className="mt-3 space-y-4 rounded-lg border border-slate-200 bg-white p-6">
          <div>
            <label className="block text-sm font-medium text-slate-700">Token name</label>
            <input value={keyName} onChange={(e) => setKeyName(e.target.value)} placeholder="CI pipeline" className={inputCls} />
          </div>
          <div>
            <span className="block text-sm font-medium text-slate-700">Scopes</span>
            <div className="mt-2 flex flex-wrap gap-3">
              {SCOPES.map((s) => (
                <label key={s} className="flex items-center gap-1.5 text-sm text-slate-600">
                  <input type="checkbox" checked={keyScopes.includes(s)} onChange={() => toggle(keyScopes, setKeyScopes, s)} />
                  <code className="font-mono text-xs">{s}</code>
                </label>
              ))}
            </div>
          </div>
          {keyErr && <p className="text-sm text-red-600">Could not create token: {keyErr}</p>}
          <button type="submit" className={btnCls} disabled={keyScopes.length === 0}>Create token</button>
        </form>

        <div className="mt-4 overflow-hidden rounded-lg border border-slate-200 bg-white">
          {keys.length === 0 ? (
            <p className="p-4 text-sm text-slate-400">No tokens yet.</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-400">
                <tr>
                  <th className="px-4 py-2 font-medium">Name</th>
                  <th className="px-4 py-2 font-medium">Prefix</th>
                  <th className="px-4 py-2 font-medium">Scopes</th>
                  <th className="px-4 py-2" />
                </tr>
              </thead>
              <tbody>
                {keys.map((k) => (
                  <tr key={k.id} className="border-b border-slate-50 last:border-0">
                    <td className="px-4 py-2 font-medium text-slate-700">{k.name}</td>
                    <td className="px-4 py-2 font-mono text-xs text-slate-500">{k.prefix}…</td>
                    <td className="px-4 py-2 font-mono text-xs text-slate-500">{k.scopes.join(' ')}</td>
                    <td className="px-4 py-2 text-right">
                      <button onClick={() => revokeKey(k.id)} className="text-xs font-medium text-red-600 hover:underline">
                        Revoke
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>

      {/* ---------------- Webhooks ---------------- */}
      <section className="mt-10">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Webhooks</h2>

        {newSecret && (
          <div className="mt-3 rounded-lg border border-amber-300 bg-amber-50 p-4">
            <p className="text-sm font-medium text-amber-800">
              Signing secret (shown once). Use it to verify the <code>X-VF-Signature</code> header.
            </p>
            <code className="mt-2 block break-all rounded bg-white px-3 py-2 font-mono text-sm text-slate-800">
              {newSecret}
            </code>
          </div>
        )}

        <form onSubmit={createHook} className="mt-3 space-y-4 rounded-lg border border-slate-200 bg-white p-6">
          <div>
            <label className="block text-sm font-medium text-slate-700">Payload URL</label>
            <input value={hookUrl} onChange={(e) => setHookUrl(e.target.value)} placeholder="https://example.com/hooks" required className={inputCls} />
          </div>
          <div>
            <span className="block text-sm font-medium text-slate-700">Events</span>
            <div className="mt-2 flex flex-wrap gap-3">
              {EVENTS.map((ev) => (
                <label key={ev} className="flex items-center gap-1.5 text-sm text-slate-600">
                  <input type="checkbox" checked={hookEvents.includes(ev)} onChange={() => toggle(hookEvents, setHookEvents, ev)} />
                  <code className="font-mono text-xs">{ev}</code>
                </label>
              ))}
            </div>
          </div>
          {hookErr && <p className="text-sm text-red-600">Could not create webhook: {hookErr}</p>}
          <button type="submit" className={btnCls}>Add webhook</button>
        </form>

        <div className="mt-4 space-y-3">
          {hooks.length === 0 ? (
            <p className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-400">No webhooks yet.</p>
          ) : (
            hooks.map((h) => (
              <div key={h.id} className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="truncate font-mono text-sm text-slate-700">{h.url}</p>
                    <p className="mt-1 text-xs text-slate-400">
                      {h.events.length ? h.events.join(', ') : 'all events'} · secret {h.secret}
                    </p>
                    {testResult[h.id] && <p className="mt-1 text-xs text-slate-500">{testResult[h.id]}</p>}
                  </div>
                  <div className="flex shrink-0 gap-3 text-xs font-medium">
                    <button onClick={() => testHook(h.id)} className="text-brand-600 hover:underline">Test</button>
                    <button onClick={() => deleteHook(h.id)} className="text-red-600 hover:underline">Delete</button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </section>
    </div>
  )
}
