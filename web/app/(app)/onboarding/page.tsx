'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useApi } from '@/components/Providers'

const STEPS = ['Welcome', 'Workspace', 'First project', 'Done']

export default function OnboardingPage() {
  const { apiFetch } = useApi()
  const router = useRouter()

  const [step, setStep] = useState(0)
  const [orgName, setOrgName] = useState('')
  const [projectName, setProjectName] = useState('')
  const [busy, setBusy] = useState(false)

  async function saveOrg() {
    if (!orgName.trim()) return setStep(2)
    setBusy(true)
    await apiFetch('/api/org', {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: orgName }),
    })
    setBusy(false)
    setStep(2)
  }

  async function createProject() {
    if (!projectName.trim()) return setStep(3)
    setBusy(true)
    await apiFetch('/api/projects', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: projectName }),
    })
    setBusy(false)
    setStep(3)
  }

  const input = 'mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500'
  const primary = 'rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50'
  const ghost = 'rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100'

  return (
    <div className="mx-auto max-w-lg">
      <ol className="flex items-center gap-2 text-xs">
        {STEPS.map((label, i) => (
          <li key={label} className="flex items-center gap-2">
            <span className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold
              ${i <= step ? 'bg-brand-600 text-white' : 'bg-slate-200 text-slate-500'}`}>{i + 1}</span>
            <span className={i <= step ? 'text-slate-900' : 'text-slate-400'}>{label}</span>
            {i < STEPS.length - 1 && <span className="mx-1 h-px w-6 bg-slate-200" />}
          </li>
        ))}
      </ol>

      <div className="mt-8 rounded-lg border border-slate-200 bg-white p-8">
        {step === 0 && (
          <div>
            <h1 className="text-2xl font-bold">Welcome to Prolane 👋</h1>
            <p className="mt-2 text-slate-600">Let&apos;s get your workspace set up in a couple of quick steps.</p>
            <button onClick={() => setStep(1)} className={`mt-6 ${primary}`}>Get started</button>
          </div>
        )}

        {step === 1 && (
          <div>
            <h1 className="text-xl font-bold">Name your workspace</h1>
            <p className="mt-1 text-sm text-slate-500">You can change this later in organization settings.</p>
            <input value={orgName} onChange={(e) => setOrgName(e.target.value)} placeholder="Your company" className={input} />
            <div className="mt-6 flex gap-2">
              <button onClick={() => setStep(2)} className={ghost}>Skip</button>
              <button onClick={saveOrg} disabled={busy} className={primary}>{busy ? 'Saving…' : 'Continue'}</button>
            </div>
          </div>
        )}

        {step === 2 && (
          <div>
            <h1 className="text-xl font-bold">Create your first project</h1>
            <p className="mt-1 text-sm text-slate-500">Projects organize your team&apos;s work.</p>
            <input value={projectName} onChange={(e) => setProjectName(e.target.value)} placeholder="Website Redesign" className={input} />
            <div className="mt-6 flex gap-2">
              <button onClick={() => setStep(3)} className={ghost}>Skip</button>
              <button onClick={createProject} disabled={busy} className={primary}>{busy ? 'Creating…' : 'Continue'}</button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div>
            <h1 className="text-2xl font-bold">You&apos;re all set 🎉</h1>
            <p className="mt-2 text-slate-600">Your workspace is ready. Jump into your dashboard to start working.</p>
            <button onClick={() => { router.push('/dashboard'); router.refresh() }} className={`mt-6 ${primary}`}>
              Go to dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
