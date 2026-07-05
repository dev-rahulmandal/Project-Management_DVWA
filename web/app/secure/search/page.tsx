'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'

export default function SecureSearchPage() {
  const ref = useRef<HTMLDivElement>(null)
  const [term, setTerm] = useState('')

  useEffect(() => {
    const render = () => {
      const q = decodeURIComponent(window.location.hash.slice(1))
      if (ref.current) {
        ref.current.textContent = q
          ? `Showing results for: ${q}`
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
