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

export function TaskRows({ tasks, renderRichText = false }: { tasks: Task[]; renderRichText?: boolean }) {
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
              (renderRichText ? (
                <p
                  className="mt-0.5 text-sm text-slate-500"
                  dangerouslySetInnerHTML={{ __html: t.body }}
                />
              ) : (
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
