'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

// WEB-PROTO-001: prototype pollution.
// A user-supplied JSON config (?config=) is deep-merged into defaults with a
// recursive merge that doesn't guard __proto__/constructor. A payload like
//   {"__proto__":{"polluted":"x"}}
// writes onto Object.prototype, so EVERY object in the page then inherits it.
// Secured twin /secure/customize skips dangerous keys.
function unsafeMerge(target: Record<string, any>, source: Record<string, any>) {
  for (const key in source) {
    const val = source[key]
    if (val && typeof val === 'object') {
      if (!target[key]) target[key] = {}
      unsafeMerge(target[key], val)
    } else {
      target[key] = val
    }
  }
  return target
}

export default function CustomizePage() {
  const [polluted, setPolluted] = useState<string | null>(null)

  useEffect(() => {
    const raw = new URLSearchParams(window.location.search).get('config')
    const defaults: Record<string, any> = { theme: 'light' }
    if (raw) {
      try { unsafeMerge(defaults, JSON.parse(raw)) } catch { /* ignore */ }
    }
    // Probe a brand-new object - if it inherited `polluted`, the prototype is poisoned.
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
          ⚠ PROTOTYPE POLLUTED - every object now inherits polluted = {polluted}
        </div>
      ) : (
        <div className="mt-6 rounded-md bg-green-50 p-4 text-sm text-green-800">
          Object.prototype is clean.
        </div>
      )}
    </div>
  )
}
