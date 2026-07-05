'use client'

import { useState } from 'react'
import Link from 'next/link'

export default function EmbedPage() {
  const [status, setStatus] = useState<'idle' | 'working' | 'done'>('idle')

  const confirmDelete = () => {
    setStatus('working')
    setTimeout(() => setStatus('done'), 1200)
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-5xl px-6 py-4">
          <Link href="/" className="text-lg font-bold text-brand-600">Prolane</Link>
        </div>
      </header>

      <main className="flex flex-1 items-center justify-center px-6 py-16">
        <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
          {status === 'done' ? (
            <div className="text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
                <svg className="h-6 w-6 text-green-600" viewBox="0 0 20 20" fill="currentColor" aria-hidden>
                  <path
                    fillRule="evenodd"
                    d="M16.7 5.3a1 1 0 0 1 0 1.4l-7.5 7.5a1 1 0 0 1-1.4 0L3.3 9.7a1 1 0 1 1 1.4-1.4l3.3 3.3 6.8-6.8a1 1 0 0 1 1.4 0z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <h1 className="mt-4 text-xl font-semibold text-slate-900">Workspace scheduled for deletion</h1>
              <p className="mt-2 text-sm text-slate-600">
                Your workspace will be permanently removed in 24 hours. You can undo this from the
                recovery link we emailed to the account owner.
              </p>
              <Link
                href="/"
                className="mt-6 inline-block rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Return to Prolane
              </Link>
            </div>
          ) : (
            <>
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100">
                <svg className="h-5 w-5 text-red-600" viewBox="0 0 20 20" fill="currentColor" aria-hidden>
                  <path
                    fillRule="evenodd"
                    d="M8.3 2.3a1 1 0 0 1 .9-.5h1.6a1 1 0 0 1 .9.5l.6 1.1H15a1 1 0 1 1 0 2h-.3l-.7 9.3a2 1 0 0 1-2 1.8H8a2 1 0 0 1-2-1.8L5.3 5H5a1 1 0 0 1 0-2h2.7l.6-.7zM9 7a1 1 0 0 1 1 1v5a1 1 0 1 1-2 0V8a1 1 0 0 1 1-1z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <h1 className="mt-4 text-xl font-semibold text-slate-900">Delete workspace</h1>
              <p className="mt-2 text-sm text-slate-600">
                You are about to permanently delete your workspace along with every project, task,
                comment, and file it contains. This action cannot be undone once the 24-hour recovery
                window closes.
              </p>
              <div className="mt-8 flex justify-end gap-3">
                <Link
                  href="/dashboard"
                  className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </Link>
                <button
                  onClick={confirmDelete}
                  disabled={status === 'working'}
                  className="inline-flex items-center gap-2 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-60"
                >
                  {status === 'working' && (
                    <svg className="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden>
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 0 1 8-8V0C5.4 0 0 5.4 0 12h4z" />
                    </svg>
                  )}
                  {status === 'working' ? 'Deleting workspace' : 'Delete workspace'}
                </button>
              </div>
            </>
          )}
        </div>
      </main>
    </div>
  )
}
