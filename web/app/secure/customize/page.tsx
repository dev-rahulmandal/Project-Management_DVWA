'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

// WEB-PROTO-001-SAFE (secured twin): same deep-merge, but dangerous keys
// (__proto__, constructor, prototype) are skipped, so a malicious config can
// never reach Object.prototype.
const BLOCKED = new Set(['__proto__', 'constructor', 'prototype'])

function safeMerge(target: Record<string, any>, source: Record<string, any>) {
  for (const key in source) {
    if (BLOCKED.has(key)) continue
    const val = source[key]
    if (val && typeof val === 'object') {
      if (!target[key]) target[key] = {}
      safeMerge(target[key], val)
    } else {
      target[key] = val
    }
  }
  return target
}

export default function SecureCustomizePage() {
  const [polluted, setPolluted] = useState<string | null>(null)

  useEffect(() => {
    const raw = new URLSearchParams(window.location.search).get('config')
    const defaults: Record<string, any> = { theme: 'light' }
    if (raw) {
      try { safeMerge(defaults, JSON.parse(raw)) } catch { /* ignore */ }
    }
    const probe: any = {}
    setPolluted(typeof probe.polluted === 'string' ? probe.polluted : null)
  }, [])

  return (
    <div className="mx-auto max-w-2xl px-6 py-12">
      <Link href="/" className="text-sm text-brand-600 hover:underline">← Home</Link>
      <h1 className="mt-4 text-2xl font-bold">Customize your workspace</h1>
      <p className="mt-2 text-slate-600">
        Apply a theme config via the <code>?config=</code> URL parameter.
      </p>
      {polluted ? (
        <div className="mt-6 rounded-md bg-red-600 p-4 font-bold text-white">
          ⚠ PROTOTYPE POLLUTED - polluted = {polluted}
        </div>
      ) : (
        <div className="mt-6 rounded-md bg-green-50 p-4 text-sm text-green-800">
          Object.prototype is clean.
        </div>
      )}
    </div>
  )
}
