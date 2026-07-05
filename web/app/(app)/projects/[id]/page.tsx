'use client'

import { useCallback, useEffect, useState } from 'react'
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

interface Attachment {
  id: number
  filename: string
  contentType: string | null
  sizeBytes: number
}

function fmtSize(n: number): string {
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / 1024 / 1024).toFixed(1)} MB`
}

export default function ProjectDetailPage() {
  const { apiFetch, ready } = useApi()
  const params = useParams()
  const id = String(params.id)

  const [project, setProject] = useState<Project | null>(null)
  const [tasks, setTasks] = useState<Task[] | null>(null)
  const [error, setError] = useState('')

  const [showForm, setShowForm] = useState(false)
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [priority, setPriority] = useState('medium')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')

  const [attachments, setAttachments] = useState<Attachment[] | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState('')

  const loadTasks = useCallback(() => {
    apiFetch(`/api/projects/${id}/tasks`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error())))
      .then((d) => setTasks(d.tasks))
      .catch(() => setTasks([]))
  }, [apiFetch, id])

  const loadAttachments = useCallback(() => {
    apiFetch(`/api/projects/${id}/attachments`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error())))
      .then((d) => setAttachments(d.attachments))
      .catch(() => setAttachments([]))
  }, [apiFetch, id])

  useEffect(() => {
    if (!ready) return

    apiFetch(`/api/projects/${id}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d) => setProject(d.project))
      .catch((e) => setError(String(e.message ?? e)))

    loadTasks()
    loadAttachments()
  }, [ready, apiFetch, id, loadTasks, loadAttachments])

  async function uploadFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setUploadError('')
    try {
      const fd = new FormData()
      fd.append('file', file)
      const r = await apiFetch(`/api/projects/${id}/attachments`, { method: 'POST', body: fd })
      if (!r.ok) {
        const d = await r.json().catch(() => ({}))
        throw new Error(d.detail === 'file_too_large' ? 'File exceeds 10 MB.' : `HTTP ${r.status}`)
      }
      loadAttachments()
    } catch (err) {
      setUploadError(String((err as Error).message ?? err))
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  async function downloadFile(att: Attachment) {
    const r = await apiFetch(`/api/attachments/${att.id}/download`)
    if (!r.ok) return
    const blob = await r.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = att.filename
    a.click()
    URL.revokeObjectURL(url)
  }

  async function deleteFile(att: Attachment) {
    await apiFetch(`/api/attachments/${att.id}`, { method: 'DELETE' })
    loadAttachments()
  }

  async function createTask(e: React.FormEvent) {
    e.preventDefault()
    setCreating(true)
    setCreateError('')
    try {
      const r = await apiFetch(`/api/projects/${id}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, body: body || null, priority }),
      })
      if (!r.ok) throw new Error(`HTTP ${r.status}`)
      setTitle('')
      setBody('')
      setPriority('medium')
      setShowForm(false)
      loadTasks()
    } catch (err) {
      setCreateError(String((err as Error).message ?? err))
    } finally {
      setCreating(false)
    }
  }

  return (
    <div>
      <Link href="/dashboard" className="text-sm text-brand-600 hover:underline">
        ← Back to projects
      </Link>

      {error && <p className="mt-6 text-sm text-red-600">Failed to load project: {error}</p>}
      {!error && !project && <p className="mt-6 text-sm text-slate-400">Loading…</p>}

      {project && (
        <>
          <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{project.name}</h1>
              <Badge text={project.status} tone={project.status === 'active' ? 'green' : 'slate'} />
            </div>
            <Link
              href={`/projects/${id}/settings`}
              className="rounded-md border border-slate-300 px-3 py-1 text-sm font-medium text-slate-700 hover:bg-slate-100"
            >
              Settings
            </Link>
          </div>
          {project.description && (
            <p className="mt-2 text-slate-600">{project.description}</p>
          )}
          <p className="mt-1 text-xs text-slate-400">Organization #{project.orgId}</p>

          <section className="mt-8">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
                Tasks
              </h2>
              <button
                onClick={() => setShowForm((v) => !v)}
                className="rounded-md border border-slate-300 px-3 py-1 text-sm font-medium text-slate-700 hover:bg-slate-100"
              >
                {showForm ? 'Cancel' : 'Add task'}
              </button>
            </div>

            {showForm && (
              <form
                onSubmit={createTask}
                className="mt-3 space-y-3 rounded-lg border border-slate-200 bg-white p-5"
              >
                <div>
                  <label htmlFor="title" className="block text-sm font-medium text-slate-700">
                    Title
                  </label>
                  <input
                    id="title"
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    required
                    className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label htmlFor="body" className="block text-sm font-medium text-slate-700">
                    Details
                  </label>
                  <textarea
                    id="body"
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                    rows={2}
                    className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                    placeholder="Supports rich text"
                  />
                </div>
                <div>
                  <label htmlFor="priority" className="block text-sm font-medium text-slate-700">
                    Priority
                  </label>
                  <select
                    id="priority"
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="mt-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
                {createError && (
                  <p className="text-sm text-red-600">Could not add task: {createError}</p>
                )}
                <button
                  type="submit"
                  disabled={creating}
                  className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
                >
                  {creating ? 'Adding…' : 'Add task'}
                </button>
              </form>
            )}

            {!tasks && <p className="mt-3 text-sm text-slate-400">Loading tasks…</p>}
            {tasks && <TaskRows tasks={tasks} renderRichText />}
          </section>

          <section className="mt-10">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
                Attachments
              </h2>
              <label className="cursor-pointer rounded-md border border-slate-300 px-3 py-1 text-sm font-medium text-slate-700 hover:bg-slate-100">
                {uploading ? 'Uploading…' : 'Upload file'}
                <input type="file" className="hidden" onChange={uploadFile} disabled={uploading} />
              </label>
            </div>

            {uploadError && <p className="mt-2 text-sm text-red-600">{uploadError}</p>}

            {!attachments && <p className="mt-3 text-sm text-slate-400">Loading attachments…</p>}
            {attachments && attachments.length === 0 && (
              <p className="mt-3 text-sm text-slate-400">No files attached yet.</p>
            )}
            {attachments && attachments.length > 0 && (
              <ul className="mt-3 divide-y divide-slate-200 overflow-hidden rounded-lg border border-slate-200 bg-white">
                {attachments.map((a) => (
                  <li key={a.id} className="flex items-center justify-between px-5 py-3">
                    <div className="min-w-0">
                      <p className="truncate font-medium text-slate-900">{a.filename}</p>
                      <p className="text-xs text-slate-500">
                        {fmtSize(a.sizeBytes)}{a.contentType ? ` · ${a.contentType}` : ''}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      <button
                        onClick={() => downloadFile(a)}
                        className="rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100"
                      >
                        Download
                      </button>
                      <button
                        onClick={() => deleteFile(a)}
                        className="rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium text-red-600 hover:bg-red-50"
                      >
                        Delete
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  )
}
