import Link from 'next/link'
import { Badge } from './Badge'

export interface Task {
  id: number
  title: string
  body: string | null
  status: string
  priority: string
  assigneeId: number | null
}

const priorityTone = (p: string) =>
  p === 'high' ? 'red' : p === 'medium' ? 'amber' : 'slate'

// Renders a project's task list.
//
// WEB-XSS-001: when `unsafe` is set, the task body - arbitrary text stored by
// any org member via POST /api/projects/{id}/tasks - is injected as raw HTML
// with dangerouslySetInnerHTML ("rich-text notes"). A payload such as
//   <img src=x onerror="...">
// stored in one member's task executes in every org member's browser that opens
// the project. The secured twin (TaskRows without `unsafe`) renders the body as
// React-escaped text, so the same stored payload is inert.
export function TaskRows({ tasks, unsafe = false }: { tasks: Task[]; unsafe?: boolean }) {
  if (tasks.length === 0) {
    return <p className="mt-3 text-sm text-slate-400">No tasks for this project.</p>
  }
  return (
    <ul className="mt-3 divide-y divide-slate-200 overflow-hidden rounded-lg border border-slate-200 bg-white">
      {tasks.map((t) => (
        <li key={t.id} className="flex items-start justify-between px-5 py-4">
          <div>
            <Link href={`/tasks/${t.id}`} className="font-medium text-slate-900 hover:text-brand-700 hover:underline">
              {t.title}
            </Link>
            {t.body &&
              (unsafe ? (
                // VULNERABLE sink - stored XSS.
                <p
                  className="mt-0.5 text-sm text-slate-500"
                  dangerouslySetInnerHTML={{ __html: t.body }}
                />
              ) : (
                // SAFE - React escapes the stored body.
                <p className="mt-0.5 text-sm text-slate-500">{t.body}</p>
              ))}
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <Badge text={t.priority} tone={priorityTone(t.priority)} />
            <Badge text={t.status.replace('_', ' ')} tone="slate" />
          </div>
        </li>
      ))}
    </ul>
  )
}
