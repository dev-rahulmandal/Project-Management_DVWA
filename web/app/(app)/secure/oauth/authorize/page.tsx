// WEB-OPENREDIR-001-SAFE - secure twin of /oauth/authorize.
// Identical to the canonical consent page except denied() validates the
// redirect_uri against the client's registered allowlist before navigating,
// so a client-supplied off-site redirect_uri cannot bounce the user away.
'use client'

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { useApi } from '@/components/Providers'

interface ClientMeta { clientId: string; name: string; logoUri: string | null; redirectUris: string[] }
interface Me { email: string; fullName: string }

function Consent() {
  const { apiFetch, ready } = useApi()
  const params = useSearchParams()

  const clientId = params.get('client_id') ?? ''
  const redirectUri = params.get('redirect_uri') ?? ''
  const scope = params.get('scope') ?? 'openid profile'
  const state = params.get('state') ?? ''
  const codeChallenge = params.get('code_challenge') ?? undefined
  const codeChallengeMethod = params.get('code_challenge_method') ?? 'S256'

  const [client, setClient] = useState<ClientMeta | null>(null)
  const [me, setMe] = useState<Me | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!ready || !clientId) return
    apiFetch(`/api/oauth/clients/${encodeURIComponent(clientId)}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('invalid_client'))))
      .then(setClient)
      .catch((e) => setError(String(e.message ?? e)))
    apiFetch('/api/me')
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => d && setMe(d))
  }, [ready, clientId, apiFetch])

  function denied() {
    if (!redirectUri) return
    // Secure twin: only bounce back to a redirect_uri the client actually
    // registered (exact allowlist match); otherwise stay in-app.
    if (!client || !client.redirectUris.includes(redirectUri)) {
      window.location.href = '/dashboard'
      return
    }
    const u = new URL(redirectUri)
    u.searchParams.set('error', 'access_denied')
    if (state) u.searchParams.set('state', state)
    window.location.href = u.toString()
  }

  async function allow() {
    setBusy(true)
    setError('')
    try {
      const r = await apiFetch('/api/oauth/authorize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ clientId, redirectUri, scope, state, codeChallenge, codeChallengeMethod }),
      })
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.detail ?? `HTTP ${r.status}`)
      const u = new URL(d.redirectUri)
      u.searchParams.set('code', d.code)
      if (d.state) u.searchParams.set('state', d.state)
      window.location.href = u.toString()
    } catch (err) {
      setError(String((err as Error).message ?? err))
      setBusy(false)
    }
  }

  if (!clientId || !redirectUri) {
    return <p className="text-sm text-red-600">Missing client_id or redirect_uri.</p>
  }

  return (
    <div className="mx-auto max-w-md">
      <div className="rounded-lg border border-slate-200 bg-white p-8">
        <h1 className="text-center text-lg font-semibold text-slate-800">
          Authorize {client?.name ?? clientId}
        </h1>
        <p className="mt-2 text-center text-sm text-slate-500">
          <span className="font-medium text-slate-700">{client?.name ?? clientId}</span> wants to access your
          Prolane account{me ? <> as <span className="font-medium">{me.email}</span></> : ''}.
        </p>

        <div className="mt-6 rounded-md border border-slate-100 bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">This will allow it to</p>
          <ul className="mt-2 space-y-1 text-sm text-slate-600">
            {scope.split(/\s+/).filter(Boolean).map((s) => (
              <li key={s} className="flex items-center gap-2">
                <span className="text-brand-600">•</span> <code className="font-mono text-xs">{s}</code>
              </li>
            ))}
          </ul>
          <p className="mt-3 break-all text-xs text-slate-400">Redirects to {redirectUri}</p>
        </div>

        {error && <p className="mt-4 text-center text-sm text-red-600">{error}</p>}

        <div className="mt-6 flex gap-3">
          <button onClick={denied} disabled={busy}
            className="flex-1 rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-50">
            Deny
          </button>
          <button onClick={allow} disabled={busy}
            className="flex-1 rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50">
            {busy ? 'Authorizing…' : 'Allow'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function AuthorizePage() {
  return (
    <Suspense fallback={<p className="text-sm text-slate-400">Loading…</p>}>
      <Consent />
    </Suspense>
  )
}
