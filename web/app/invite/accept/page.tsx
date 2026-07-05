'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'

function mapError(code?: string): string {
  switch (code) {
    case 'invalid_token': return 'This invite link is invalid.'
    case 'expired': return 'This invite has expired.'
    case 'email_taken': return 'An account for this email already exists.'
    case 'invalid_input': return 'Please enter your name and a password of at least 8 characters.'
    default: return 'Could not accept the invitation.'
  }
}

export default function AcceptInvitePage() {
  const router = useRouter()
  const [token, setToken] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    setToken(new URLSearchParams(window.location.search).get('token') ?? '')
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const { csrfToken } = await (await fetch('/api/auth/csrf')).json()
      const res = await fetch('/api/auth/accept-invite', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'fetch',
          'X-CSRF-Token': csrfToken,
        },
        credentials: 'same-origin',
        body: JSON.stringify({ token, fullName, password }),
      })
      if (res.ok) {
        router.push('/dashboard')
        router.refresh()
      } else {
        const data = await res.json().catch(() => ({}))
        setError(mapError(data.error))
      }
    } catch {
      setError('Network error')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-6">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <Link href="/" className="text-xl font-bold text-brand-600">Prolane</Link>
          <h1 className="mt-4 text-2xl font-semibold">Accept your invitation</h1>
          <p className="mt-1 text-sm text-slate-500">Set up your account to join the workspace.</p>
        </div>

        {!token && (
          <p className="mb-4 rounded-md bg-amber-50 p-3 text-sm text-amber-800">
            No invite token in the link. Ask your admin for a fresh invite.
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
          <div>
            <label className="block text-sm font-medium text-slate-700">Full name</label>
            <input
              type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} required
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              placeholder="Ada Lovelace"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Password</label>
            <input
              type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8}
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              placeholder="At least 8 characters"
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button
            type="submit" disabled={busy || !token}
            className="w-full rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {busy ? 'Joining…' : 'Join workspace'}
          </button>
        </form>
      </div>
    </div>
  )
}
