'use client'

import * as DropdownMenu from '@radix-ui/react-dropdown-menu'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { IconGear, IconLogout } from './icons'

/** Topbar account dropdown: identity header, Settings link, Sign out. */
export function UserMenu({ email, role }: { email: string; role: string }) {
  const router = useRouter()

  async function logout() {
    await fetch('/api/auth/logout', { method: 'POST' })
    router.push('/login')
    router.refresh()
  }

  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button className="flex items-center gap-2 rounded-md p-1 hover:bg-slate-100" aria-label="Account menu">
          <span className="grid h-7 w-7 place-items-center rounded-full bg-brand-100 text-xs font-semibold text-brand-700">
            {email[0]?.toUpperCase() ?? '?'}
          </span>
          <span className="hidden text-left leading-tight sm:block">
            <span className="block max-w-[140px] truncate text-xs font-medium text-slate-700">{email}</span>
            <span className="block text-[10px] uppercase tracking-wide text-slate-400">{role}</span>
          </span>
        </button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content
          align="end"
          sideOffset={8}
          className="z-50 min-w-[200px] overflow-hidden rounded-xl border border-slate-200 bg-white p-1 shadow-lg"
        >
          <div className="px-2.5 py-2">
            <p className="truncate text-sm font-medium text-slate-900">{email}</p>
            <p className="text-xs capitalize text-slate-400">{role}</p>
          </div>
          <DropdownMenu.Separator className="my-1 h-px bg-slate-100" />
          <DropdownMenu.Item asChild>
            <Link
              href="/settings"
              className="flex cursor-pointer items-center gap-2 rounded-md px-2.5 py-1.5 text-sm text-slate-700 outline-none data-[highlighted]:bg-slate-100"
            >
              <IconGear size={16} /> Settings
            </Link>
          </DropdownMenu.Item>
          <DropdownMenu.Separator className="my-1 h-px bg-slate-100" />
          <DropdownMenu.Item
            onSelect={logout}
            className="flex cursor-pointer items-center gap-2 rounded-md px-2.5 py-1.5 text-sm text-red-600 outline-none data-[highlighted]:bg-red-50"
          >
            <IconLogout size={16} /> Sign out
          </DropdownMenu.Item>
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  )
}
