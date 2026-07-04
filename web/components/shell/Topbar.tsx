'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { CommandPalette } from './CommandPalette'
import { NotificationsMenu } from './NotificationsMenu'
import { UserMenu } from './UserMenu'
import { IconChevronRight, IconGrid, IconSearch } from './icons'

const LABELS: Record<string, string> = {
  dashboard: 'Dashboard',
  projects: 'Projects',
  tasks: 'Tasks',
  activity: 'Activity',
  members: 'Members',
  team: 'Team',
  billing: 'Billing',
  developer: 'Developer',
  notifications: 'Notifications',
  settings: 'Settings',
  admin: 'Admin',
  organization: 'Organization',
  oauth: 'OAuth',
  authorize: 'Authorize',
  onboarding: 'Onboarding',
}

function labelFor(segment: string) {
  if (LABELS[segment]) return LABELS[segment]
  if (/^\d+$/.test(segment) || segment.length > 16) return segment
  return segment.charAt(0).toUpperCase() + segment.slice(1)
}

function buildCrumbs(pathname: string) {
  const parts = pathname.split('/').filter(Boolean)
  let href = ''
  return parts.map((part) => {
    href += '/' + part
    return { label: labelFor(part), href }
  })
}

export function Topbar({ email, role }: { email: string; role: string }) {
  const pathname = usePathname()
  const crumbs = buildCrumbs(pathname)

  return (
    <header className="sticky top-0 z-10 flex h-14 items-center justify-between gap-4 border-b border-slate-200 bg-white/80 px-6 backdrop-blur">
      <nav aria-label="Breadcrumb" className="flex min-w-0 items-center gap-1 text-sm">
        <Link href="/dashboard" className="text-slate-400 hover:text-slate-600" aria-label="Dashboard">
          <IconGrid size={16} />
        </Link>
        {crumbs.map((c, i) => {
          const last = i === crumbs.length - 1
          return (
            <span key={c.href} className="flex min-w-0 items-center gap-1">
              <span className="text-slate-300">
                <IconChevronRight size={14} />
              </span>
              {last ? (
                <span className="truncate font-medium text-slate-900">{c.label}</span>
              ) : (
                <Link href={c.href} className="truncate text-slate-500 hover:text-slate-800">
                  {c.label}
                </Link>
              )}
            </span>
          )
        })}
      </nav>

      <div className="flex shrink-0 items-center gap-2">
        <button
          type="button"
          onClick={() => window.dispatchEvent(new CustomEvent('vf-open-command'))}
          title="Search (Ctrl/⌘ K)"
          className="hidden items-center gap-2 rounded-md border border-slate-200 px-2.5 py-1.5 text-xs text-slate-500 hover:bg-slate-50 sm:flex"
        >
          <IconSearch size={14} />
          Search
          <kbd className="rounded border border-slate-200 bg-slate-50 px-1 font-mono text-[10px]">⌘K</kbd>
        </button>

        <NotificationsMenu />

        <div className="border-l border-slate-200 pl-1">
          <UserMenu email={email} role={role} />
        </div>
      </div>

      <CommandPalette />
    </header>
  )
}
