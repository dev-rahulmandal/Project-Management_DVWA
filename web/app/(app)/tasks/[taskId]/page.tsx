'use client'

import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { useApi } from '@/components/Providers'

interface Task {
  id: number; projectId: number; title: string; body: string | null
  status: string; priority: string; assigneeId: number | null; dueDate: string | null
}
interface Member { id: number; fullName: string }
interface Comment { id: number; body: string; authorName: string; createdAt: string }

export default function TaskDetailPage() {
  const { apiFetch, ready } = useApi()
  const taskId = String(useParams().taskId)

  const [task, setTask] = useState<Task | null>(null)
  const [members, setMembers] = useState<Member[]>([])
  const [comments, setComments] = useState<Comment[] | null>(null)
  const [error, setError] = useState('')
  const [newComment, setNewComment] = useState('')

  const loadTask = useCallback(() => {
    apiFetch(`/api/tasks/${taskId}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then((d) => setTask(d.task))
      .catch((e) => setError(String(e.message ?? e)))
  }, [apiFetch, taskId])

  const loadComments = useCallback(() => {
    apiFetch(`/api/tasks/${taskId}/comments`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error())))
      .then((d) => setComments(d.comments))
      .catch(() => setComments([]))
  }, [apiFetch, taskId])

  useEffect(() => {
    if (!ready) return
    loadTask()
    loadComments()
    apiFetch('/api/users')
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error())))
      .then((d) => setMembers(d.users))
      .catch(() => setMembers([]))
  }, [ready, apiFetch, loadTask, loadComments])

  async function patchTask(payload: object) {
    const r = await apiFetch(`/api/tasks/${taskId}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (r.ok) setTask((await r.json()).task)
  }

  async function addComment(e: React.FormEvent) {
    e.preventDefault()
    if (!newComment.trim()) return
    const r = await apiFetch(`/api/tasks/${taskId}/comments`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ body: newComment }),
    })
    if (r.ok) { setNewComment(''); loadComments() }
  }

  if (error) return <p className="text-sm text-red-600">Failed to load task: {error}</p>
  if (!task) return <p className="text-sm text-slate-400">Loading…</p>

  const field = 'rounded-md border border-slate-300 px-2 py-1 text-sm'

  return (
    <div className="max-w-3xl">
      <Link href={`/projects/${task.projectId}`} className="text-sm text-brand-600 hover:underline">
        ← Back to project
      </Link>

      <input
        value={task.title}
        onChange={(e) => setTask({ ...task, title: e.target.value })}
        onBlur={() => patchTask({ title: task.title })}
        className="mt-4 w-full rounded-md border border-transparent bg-transparent text-2xl font-bold hover:border-slate-200 focus:border-slate-300 focus:outline-none"
      />

      <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <label className="text-sm">
          <span className="block text-xs uppercase tracking-wide text-slate-400">Status</span>
          <select value={task.status} onChange={(e) => patchTask({ status: e.target.value })} className={`mt-1 w-full ${field}`}>
            <option value="open">Open</option>
            <option value="in_progress">In progress</option>
            <option value="done">Done</option>
          </select>
        </label>
        <label className="text-sm">
          <span className="block text-xs uppercase tracking-wide text-slate-400">Priority</span>
          <select value={task.priority} onChange={(e) => patchTask({ priority: e.target.value })} className={`mt-1 w-full ${field}`}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </label>
        <label className="text-sm">
          <span className="block text-xs uppercase tracking-wide text-slate-400">Assignee</span>
          <select
            value={task.assigneeId ?? ''}
            onChange={(e) => patchTask({ assigneeId: Number(e.target.value) })}
            className={`mt-1 w-full ${field}`}
          >
            <option value="" disabled>Unassigned</option>
            {members.map((m) => <option key={m.id} value={m.id}>{m.fullName}</option>)}
          </select>
        </label>
        <label className="text-sm">
          <span className="block text-xs uppercase tracking-wide text-slate-400">Due date</span>
          <input
            type="date" value={task.dueDate ?? ''}
            onChange={(e) => patchTask({ dueDate: e.target.value })}
            className={`mt-1 w-full ${field}`}
          />
        </label>
      </div>

      <div className="mt-6">
        <span className="block text-xs uppercase tracking-wide text-slate-400">Details</span>
        <textarea
          value={task.body ?? ''}
          onChange={(e) => setTask({ ...task, body: e.target.value })}
          onBlur={() => patchTask({ body: task.body })}
          rows={3}
          className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
        />
      </div>

      <section className="mt-8">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Comments</h2>
        {comments && comments.length > 0 && (
          <ul className="mt-3 space-y-3">
            {comments.map((c) => (
              <li key={c.id} className="rounded-lg border border-slate-200 bg-white p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-slate-900">{c.authorName}</span>
                  <span className="text-xs text-slate-400">{c.createdAt.slice(0, 16)}</span>
                </div>
                <p className="mt-1 text-sm text-slate-700">{c.body}</p>
              </li>
            ))}
          </ul>
        )}
        {comments && comments.length === 0 && (
          <p className="mt-3 text-sm text-slate-400">No comments yet.</p>
        )}
        <form onSubmit={addComment} className="mt-4 flex gap-2">
          <input
            value={newComment} onChange={(e) => setNewComment(e.target.value)}
            placeholder="Add a comment…"
            className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
          <button className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
            Comment
          </button>
        </form>
      </section>
    </div>
  )
}
