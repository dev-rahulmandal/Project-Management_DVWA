'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { useApi } from '@/components/Providers'
import { Badge } from '@/components/Badge'
import { TaskRows, type Task } from '@/components/TaskRows'

interface Project {
  id: number
  orgId: number
  name: string
  description: string | null
  status: string
}

export default function SecureProjectDetailPage() {
  const { apiFetch, ready } = useApi()
  const params = useParams()
  const id = String(params.id)

  const [project, setProject] = useState<Project | null>(null)
  const [tasks, setTasks] = useState<Task[] | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!ready) return

    apiFetch(`/api/projects/${id}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d) => setProject(d.project))
      .catch((e) => setError(String(e.message ?? e)))

    apiFetch(`/api/projects/${id}/tasks`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error())))
      .then((d) => setTasks(d.tasks))
      .catch(() => setTasks([]))
  }, [ready, apiFetch, id])

  return (
    <div>
      <Link href="/dashboard" className="text-sm text-brand-600 hover:underline">
        ← Back to projects
      </Link>

      {error && <p className="mt-6 text-sm text-red-600">Failed to load project: {error}</p>}
      {!error && !project && <p className="mt-6 text-sm text-slate-400">Loading…</p>}

      {project && (
        <>
          <div className="mt-4 flex items-center gap-3">
            <h1 className="text-2xl font-bold">{project.name}</h1>
            <Badge text={project.status} tone={project.status === 'active' ? 'green' : 'slate'} />
          </div>
          {project.description && <p className="mt-2 text-slate-600">{project.description}</p>}
          <p className="mt-1 text-xs text-slate-400">Organization #{project.orgId}</p>

          <section className="mt-8">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Tasks</h2>
            {!tasks && <p className="mt-3 text-sm text-slate-400">Loading tasks…</p>}
            {tasks && <TaskRows tasks={tasks} />}
          </section>
        </>
      )}
    </div>
  )
}
