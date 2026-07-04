'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'

// WEB-DOMXSS-001: DOM-based XSS.
// The search term is read from the URL fragment (location.hash) - which the
// server never sees - and written into the page with innerHTML. A crafted link
// like /search#<img src=x onerror=...> executes script in the victim's browser.
// Secured twin /secure/search renders the same value with textContent (escaped).
export default function SearchPage() {
  const ref = useRef<HTMLDivElement>(null)
  const [term, setTerm] = useState('')

  useEffect(() => {
    const render = () => {
      const q = decodeURIComponent(window.location.hash.slice(1))
      if (ref.current) {
        ref.current.innerHTML = q
          ? `Showing results for: <strong>${q}</strong>`
          : 'Enter a term to search the help center.'
      }
    }
    render()
    window.addEventListener('hashchange', render)
    return () => window.removeEventListener('hashchange', render)
  }, [])

  return (
    <div className="mx-auto max-w-2xl px-6 py-12">
      <Link href="/" className="text-sm text-brand-600 hover:underline">← Home</Link>
      <h1 className="mt-4 text-2xl font-bold">Help Center Search</h1>
      <form
        onSubmit={(e) => { e.preventDefault(); window.location.hash = encodeURIComponent(term) }}
        className="mt-4 flex gap-2"
      >
        <input
          value={term}
          onChange={(e) => setTerm(e.target.value)}
          placeholder="Search articles…"
          className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        />
        <button className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
          Search
        </button>
      </form>
      <div ref={ref} className="mt-6 text-slate-700" />
    </div>
  )
}
