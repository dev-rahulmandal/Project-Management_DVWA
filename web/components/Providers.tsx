'use client'

import {
  createContext, useCallback, useContext, useEffect, useState,
} from 'react'

const API_ORIGIN = process.env.NEXT_PUBLIC_API_ORIGIN ?? 'http://api.prolane.test:8081'

interface ApiContextValue {
  token: string | null
  ready: boolean
  apiFetch: (path: string, init?: RequestInit) => Promise<Response>
}

const ApiContext = createContext<ApiContextValue | null>(null)

export function ApiProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [ready, setReady] = useState(false)

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
