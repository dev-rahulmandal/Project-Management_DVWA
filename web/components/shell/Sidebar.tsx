'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import type { ReactNode } from 'react'
import { cn } from '@/lib/cn'
import {
  IconActivity,
  IconBolt,
  IconBuilding,
  IconCard,
  IconCheck,
  IconCode,
  IconFolder,
  IconGear,
  IconGrid,
  IconShield,
  IconUsers,
} from './icons'

interface NavItem {
  href: string
  label: string
  icon: ReactNode
}
interface NavSection {
  title: string
  items: NavItem[]
}

const BASE_SECTIONS: NavSection[] = [
  {
    title: 'Workspace',
    items: [
      { href: '/dashboard', label: 'Dashboard', icon: <IconGrid /> },
      { href: '/projects', label: 'Projects', icon: <IconFolder /> },
      { href: '/tasks', label: 'Tasks', icon: <IconCheck /> },
      { href: '/activity', label: 'Activity', icon: <IconActivity /> },
    ],
  },
  {
    title: 'Organization',
    items: [
      { href: '/members', label: 'Members', icon: <IconUsers /> },
      { href: '/billing', label: 'Billing', icon: <IconCard /> },
    ],
  },
  {
    title: 'Developer',
    items: [{ href: '/developer', label: 'API & Webhooks', icon: <IconCode /> }],
  },
]

const ADMIN_SECTION: NavSection = {
  title: 'Admin',
  items: [
    { href: '/admin', label: 'Overview', icon: <IconShield /> },
    { href: '/admin/members', label: 'Members', icon: <IconUsers /> },
    { href: '/admin/organization', label: 'Organization', icon: <IconBuilding /> },
  ],
}

export function Sidebar({ isAdmin }: { isAdmin: boolean }) {
  const pathname = usePathname()
  const sections = isAdmin ? [...BASE_SECTIONS, ADMIN_SECTION] : BASE_SECTIONS

  const isActive = (href: string) =>
    href === '/admin' ? pathname === '/admin' : pathname === href || pathname.startsWith(href + '/')

  return (
    <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-slate-200 bg-white md:flex">
      <div className="flex h-14 items-center border-b border-slate-100 px-5">
        <Link href="/dashboard" className="flex items-center gap-2 text-base font-bold text-slate-900">
          <span className="grid h-7 w-7 place-items-center rounded-lg bg-brand-600 text-white">
            <IconBolt />
          </span>
          Prolane
        </Link>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        {sections.map((section) => (
          <div key={section.title} className="mb-5">
            <p className="px-2 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              {section.title}
            </p>
            <ul className="space-y-0.5">
              {section.items.map((item) => {
                const active = isActive(item.href)
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      aria-current={active ? 'page' : undefined}
                      className={cn(
                        'flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors',
                        active
                          ? 'bg-brand-50 text-brand-700'
                          : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
                      )}
                    >
                      <span className={cn('shrink-0', active ? 'text-brand-600' : 'text-slate-400')}>
                        {item.icon}
                      </span>
                      {item.label}
                    </Link>
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-slate-100 px-3 py-3">
        <Link
          href="/settings"
          aria-current={isActive('/settings') ? 'page' : undefined}
          className={cn(
            'flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors',
            isActive('/settings')
              ? 'bg-brand-50 text-brand-700'
              : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
          )}
        >
          <span className={cn('shrink-0', isActive('/settings') ? 'text-brand-600' : 'text-slate-400')}>
            <IconGear />
          </span>
          Settings
        </Link>
      </div>
    </aside>
  )
}
