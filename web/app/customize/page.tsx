'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

type Settings = {
  theme: 'light' | 'dark' | 'system'
  accent: 'indigo' | 'blue' | 'green' | 'rose' | 'amber'
  density: 'comfortable' | 'compact'
  fontScale: 'normal' | 'large'
}

const DEFAULTS: Settings = { theme: 'light', accent: 'indigo', density: 'comfortable', fontScale: 'normal' }

const ACCENTS: Record<Settings['accent'], { label: string; swatch: string; solid: string }> = {
  indigo: { label: 'Indigo', swatch: 'bg-indigo-600', solid: 'bg-indigo-600' },
  blue: { label: 'Blue', swatch: 'bg-blue-600', solid: 'bg-blue-600' },
  green: { label: 'Green', swatch: 'bg-green-600', solid: 'bg-green-600' },
  rose: { label: 'Rose', swatch: 'bg-rose-600', solid: 'bg-rose-600' },
  amber: { label: 'Amber', swatch: 'bg-amber-500', solid: 'bg-amber-500' },
}

function mergeConfig(target: Record<string, any>, source: Record<string, any>) {
  for (const key in source) {
    const val = source[key]
    if (val && typeof val === 'object') {
      if (!target[key]) target[key] = {}
      mergeConfig(target[key], val)
    } else {
      target[key] = val
    }
  }
  return target
}

export default function CustomizePage() {
  const [settings, setSettings] = useState<Settings>(DEFAULTS)
  const [origin, setOrigin] = useState('')
  const [saved, setSaved] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    setOrigin(window.location.origin)
    const current: Record<string, any> = { ...DEFAULTS }
    try {
      const stored = JSON.parse(localStorage.getItem('prolane.appearance') || 'null')
      if (stored && typeof stored === 'object') Object.assign(current, stored)
    } catch {
    }
    const raw = new URLSearchParams(window.location.search).get('config')
    if (raw) {
      try {
        mergeConfig(current, JSON.parse(raw))
      } catch {
      }
    }
    setSettings({
      theme: current.theme ?? DEFAULTS.theme,
      accent: current.accent ?? DEFAULTS.accent,
      density: current.density ?? DEFAULTS.density,
      fontScale: current.fontScale ?? DEFAULTS.fontScale,
    })
  }, [])

  const update = (patch: Partial<Settings>) => {
    setSettings((s) => ({ ...s, ...patch }))
    setSaved(false)
    setCopied(false)
  }

  const save = () => {
    try {
      localStorage.setItem('prolane.appearance', JSON.stringify(settings))
      setSaved(true)
    } catch {
    }
  }

  const shareUrl = `${origin}/customize?config=${encodeURIComponent(JSON.stringify(settings))}`

  const copyShare = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl)
      setCopied(true)
    } catch {
      setCopied(false)
    }
  }

  const dark = settings.theme === 'dark'
  const accent = ACCENTS[settings.accent]
  const rowPad = settings.density === 'compact' ? 'py-1.5' : 'py-3'
  const baseText = settings.fontScale === 'large' ? 'text-base' : 'text-sm'

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <Link href="/" className="text-lg font-bold text-brand-600">Prolane</Link>
          <nav className="flex items-center gap-4 text-sm">
            <Link href="/pricing" className="text-slate-600 hover:text-slate-900">Pricing</Link>
            <Link href="/search" className="text-slate-600 hover:text-slate-900">Help</Link>
            <Link href="/login" className="text-slate-600 hover:text-slate-900">Sign in</Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-12">
        <h1 className="text-2xl font-bold text-slate-900">Appearance</h1>
        <p className="mt-1 text-slate-600">
          Personalize how your workspace looks. Preferences are saved to this browser, and you can
          share a theme with your team using a link.
        </p>

        <div className="mt-8 grid grid-cols-1 gap-8 lg:grid-cols-[1fr_1fr]">
          <div className="space-y-8">
            <section>
              <h2 className="text-sm font-semibold text-slate-900">Theme</h2>
              <div className="mt-3 inline-flex rounded-lg border border-slate-200 bg-white p-1 text-sm">
                {(['light', 'dark', 'system'] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => update({ theme: t })}
                    className={`rounded-md px-4 py-1.5 font-medium capitalize transition-colors ${
                      settings.theme === t ? 'bg-brand-600 text-white' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </section>

            <section>
              <h2 className="text-sm font-semibold text-slate-900">Accent color</h2>
              <div className="mt-3 flex gap-3">
                {(Object.keys(ACCENTS) as Settings['accent'][]).map((a) => (
                  <button
                    key={a}
                    onClick={() => update({ accent: a })}
                    aria-label={ACCENTS[a].label}
                    className={`h-8 w-8 rounded-full ${ACCENTS[a].swatch} ring-offset-2 transition ${
                      settings.accent === a ? 'ring-2 ring-slate-400' : 'hover:ring-2 hover:ring-slate-200'
                    }`}
                  />
                ))}
              </div>
            </section>

            <section>
              <h2 className="text-sm font-semibold text-slate-900">Density</h2>
              <div className="mt-3 inline-flex rounded-lg border border-slate-200 bg-white p-1 text-sm">
                {(['comfortable', 'compact'] as const).map((d) => (
                  <button
                    key={d}
                    onClick={() => update({ density: d })}
                    className={`rounded-md px-4 py-1.5 font-medium capitalize transition-colors ${
                      settings.density === d ? 'bg-brand-600 text-white' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </section>

            <section>
              <h2 className="text-sm font-semibold text-slate-900">Text size</h2>
              <div className="mt-3 inline-flex rounded-lg border border-slate-200 bg-white p-1 text-sm">
                {(['normal', 'large'] as const).map((f) => (
                  <button
                    key={f}
                    onClick={() => update({ fontScale: f })}
                    className={`rounded-md px-4 py-1.5 font-medium capitalize transition-colors ${
                      settings.fontScale === f ? 'bg-brand-600 text-white' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    {f}
                  </button>
                ))}
              </div>
            </section>

            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={save}
                className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
              >
                Save preferences
              </button>
              {saved && <span className="text-sm text-green-600">Saved to this browser.</span>}
            </div>
          </div>

          <div>
            <h2 className="text-sm font-semibold text-slate-900">Preview</h2>
            <div
              className={`mt-3 overflow-hidden rounded-xl border shadow-sm ${
                dark ? 'border-slate-700 bg-slate-900' : 'border-slate-200 bg-white'
              } ${baseText}`}
            >
              <div className={`flex items-center justify-between px-4 py-3 ${accent.solid}`}>
                <span className="font-semibold text-white">My Workspace</span>
                <span className="h-2.5 w-2.5 rounded-full bg-white/80" />
              </div>
              <div className="p-4">
                <p className={`font-semibold ${dark ? 'text-slate-100' : 'text-slate-900'}`}>
                  Website Redesign
                </p>
                <ul className={`mt-2 divide-y ${dark ? 'divide-slate-700' : 'divide-slate-100'}`}>
                  {['Design mockups', 'Copy review', 'OAuth setup'].map((task, i) => (
                    <li key={task} className={`flex items-center justify-between ${rowPad}`}>
                      <span className={dark ? 'text-slate-200' : 'text-slate-700'}>{task}</span>
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs ${
                          i === 0
                            ? 'bg-green-100 text-green-700'
                            : i === 1
                              ? 'bg-amber-100 text-amber-700'
                              : 'bg-slate-100 text-slate-600'
                        }`}
                      >
                        {i === 0 ? 'Done' : i === 1 ? 'In progress' : 'Open'}
                      </span>
                    </li>
                  ))}
                </ul>
                <button className={`mt-4 rounded-md px-3 py-1.5 text-sm font-medium text-white ${accent.solid}`}>
                  New task
                </button>
              </div>
            </div>

            <div className="mt-6 rounded-lg border border-slate-200 bg-white p-4">
              <h3 className="text-sm font-semibold text-slate-900">Share this theme</h3>
              <p className="mt-1 text-sm text-slate-600">
                Send this link so a teammate opens the workspace with the same appearance.
              </p>
              <div className="mt-3 flex gap-2">
                <input
                  readOnly
                  value={shareUrl}
                  className="flex-1 truncate rounded-md border border-slate-300 bg-slate-50 px-3 py-2 text-xs text-slate-600"
                />
                <button
                  onClick={copyShare}
                  className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  {copied ? 'Copied' : 'Copy'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t border-slate-200 bg-white py-8 text-center text-xs text-slate-400">
        Copyright 2026 Prolane, Inc. All rights reserved.
      </footer>
    </div>
  )
}
