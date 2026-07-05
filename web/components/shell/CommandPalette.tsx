'use client'

import * as Dialog from '@radix-ui/react-dialog'
import { Command } from 'cmdk'
import { useRouter } from 'next/navigation'
import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { useApi } from '@/components/Providers'
import { IconSearch } from './icons'

interface Item {
  id: string
  label: string
  sub?: string
  href: string
}

const NAV: Item[] = [
  { id: 'nav-dashboard', label: 'Dashboard', href: '/dashboard' },
  { id: 'nav-projects', label: 'Projects', href: '/projects' },
  { id: 'nav-tasks', label: 'Tasks', href: '/tasks' },
  { id: 'nav-activity', label: 'Activity', href: '/activity' },
  { id: 'nav-members', label: 'Members', href: '/members' },
  { id: 'nav-billing', label: 'Billing', href: '/billing' },
  { id: 'nav-developer', label: 'Developer', href: '/developer' },
  { id: 'nav-settings', label: 'Settings', href: '/settings' },
]

export function CommandPalette() {
  const router = useRouter()
  const { apiFetch, ready } = useApi()
  const [open, setOpen] = useState(false)
  const [loaded, setLoaded] = useState(false)
  const [projects, setProjects] = useState<Item[]>([])
  const [tasks, setTasks] = useState<Item[]>([])
  const [people, setPeople] = useState<Item[]>([])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((o) => !o)
      }
    }
    const onOpen = () => setOpen(true)
    document.addEventListener('keydown', onKey)
    window.addEventListener('vf-open-command', onOpen)
    return () => {
      document.removeEventListener('keydown', onKey)
      window.removeEventListener('vf-open-command', onOpen)
    }
  }, [])

  useEffect(() => {
    if (!open || loaded || !ready) return
    setLoaded(true)
    apiFetch('/api/projects')
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d?.projects)
          setProjects(
            d.projects.map((p: any) => ({ id: `p${p.id}`, label: p.name, sub: p.status, href: `/projects/${p.id}` })),
          )
      })
      .catch(() => {})
    apiFetch('/api/tasks?limit=200')
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d?.tasks)
          setTasks(
            d.tasks.map((t: any) => ({ id: `t${t.id}`, label: t.title, sub: t.projectName, href: `/tasks/${t.id}` })),
          )
      })
      .catch(() => {})
    apiFetch('/api/members')
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => {
        if (d?.members)
          setPeople(d.members.map((m: any) => ({ id: `m${m.id}`, label: m.name, sub: m.email, href: '/members' })))
      })
      .catch(() => {})
  }, [open, loaded, ready, apiFetch])

  const go = useCallback(
    (href: string) => {
      setOpen(false)
      router.push(href)
    },
    [router],
  )

  return (
    <Dialog.Root open={open} onOpenChange={setOpen}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm" />
        <Dialog.Content className="fixed left-1/2 top-[18%] z-50 w-[92vw] max-w-xl -translate-x-1/2 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-2xl focus:outline-none">
          <Dialog.Title className="sr-only">Command palette</Dialog.Title>
          <Dialog.Description className="sr-only">Search and jump to projects, tasks, people, or pages.</Dialog.Description>
          <Command label="Command palette" className="flex flex-col">
            <div className="flex items-center gap-2 border-b border-slate-100 px-4 text-slate-400">
              <IconSearch size={16} />
              <Command.Input
                autoFocus
                placeholder="Search projects, tasks, people… or jump to a page"
                className="h-12 flex-1 bg-transparent text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none"
              />
              <kbd className="rounded border border-slate-200 bg-slate-50 px-1.5 py-0.5 font-mono text-[10px] text-slate-400">
                ESC
              </kbd>
            </div>
            <Command.List className="max-h-80 overflow-y-auto p-2">
              <Command.Empty className="px-3 py-8 text-center text-sm text-slate-400">No results found.</Command.Empty>
              <PaletteGroup heading="Go to">
                {NAV.map((n) => (
                  <PaletteRow key={n.id} item={n} onSelect={() => go(n.href)} />
                ))}
              </PaletteGroup>
              {projects.length > 0 && (
                <PaletteGroup heading="Projects">
                  {projects.map((p) => (
                    <PaletteRow key={p.id} item={p} onSelect={() => go(p.href)} />
                  ))}
                </PaletteGroup>
              )}
              {tasks.length > 0 && (
                <PaletteGroup heading="Tasks">
                  {tasks.map((t) => (
                    <PaletteRow key={t.id} item={t} onSelect={() => go(t.href)} />
                  ))}
                </PaletteGroup>
              )}
              {people.length > 0 && (
                <PaletteGroup heading="People">
                  {people.map((m) => (
                    <PaletteRow key={m.id} item={m} onSelect={() => go(m.href)} />
                  ))}
                </PaletteGroup>
              )}
            </Command.List>
          </Command>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}

function PaletteGroup({ heading, children }: { heading: string; children: ReactNode }) {
  return (
    <Command.Group
      heading={heading}
      className="mb-1 [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-[11px] [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wider [&_[cmdk-group-heading]]:text-slate-400"
    >
      {children}
    </Command.Group>
  )
}

function PaletteRow({ item, onSelect }: { item: Item; onSelect: () => void }) {
  return (
    <Command.Item
      value={`${item.label} ${item.sub ?? ''}`}
      onSelect={onSelect}
      className="flex cursor-pointer items-center justify-between gap-3 rounded-md px-2.5 py-2 text-sm text-slate-700 data-[selected=true]:bg-brand-50 data-[selected=true]:text-brand-700"
    >
      <span className="truncate">{item.label}</span>
      {item.sub && <span className="shrink-0 truncate text-xs text-slate-400">{item.sub}</span>}
    </Command.Item>
  )
}
