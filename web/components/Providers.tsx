'use client'

import {
  createContext, useCallback, useContext, useEffect, useState,
} from 'react'

// The api origin the *browser* talks to (published port). Inlined at build.
const API_ORIGIN = process.env.NEXT_PUBLIC_API_ORIGIN ?? 'http://localhost:8081'

interface ApiContextValue {
  token: string | null
  ready: boolean
  /** fetch() against the api origin with the Bearer token attached. */
  apiFetch: (path: string, init?: RequestInit) => Promise<Response>
}

const ApiContext = createContext<ApiContextValue | null>(null)

export function ApiProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [ready, setReady] = useState(false)

  // On mount, exchange the httpOnly session cookie for an API Bearer token.
  // The token lives in memory only - never localStorage/sessionStorage.
  useEffect(() => {
    let cancelled = false
    fetch('/api/auth/token', { method: 'POST' })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error('no_session'))))
      .then((data) => {
        if (!cancelled) {
          setToken(data.token)
          setReady(true)
        }
      })
      .catch(() => {
        if (!cancelled) setReady(true)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const apiFetch = useCallback(
    (path: string, init: RequestInit = {}) =>
      fetch(`${API_ORIGIN}${path}`, {
        ...init,
        headers: {
          ...(init.headers ?? {}),
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      }),
    [token],
  )

  return (
    <ApiContext.Provider value={{ token, ready, apiFetch }}>
      {children}
    </ApiContext.Provider>
  )
}

export function useApi(): ApiContextValue {
  const ctx = useContext(ApiContext)
  if (!ctx) throw new Error('useApi must be used within <ApiProvider>')
  return ctx
}
