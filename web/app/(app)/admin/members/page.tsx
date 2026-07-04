'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { useApi } from '@/components/Providers'

interface Member {
  id: number; email: string; fullName: string
  role: string; isActive: boolean; isSuperAdmin: boolean
}
interface Invite { id: number; email: string; role: string; expiresAt: string }
interface Me { id: number; role: string; isSuperAdmin: boolean }

const RANK: Record<string, number> = { member: 1, admin: 2, owner: 3 }
const rankOf = (m: { role: string; isSuperAdmin: boolean }) =>
  m.isSuperAdmin ? 99 : (RANK[m.role] ?? 0)

function RoleBadge({ role }: { role: string }) {
  const styles = role === 'owner' ? 'bg-brand-50 text-brand-700'
    : role === 'admin' ? 'bg-amber-50 text-amber-700' : 'bg-slate-100 text-slate-500'
  return <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${styles}`}>{role}</span>
}

export default function MembersPage() {
  const { apiFetch, ready } = useApi()
  const [me, setMe] = useState<Me | null>(null)
  const [members, setMembers] = useState<Member[] | null>(null)
  const [invites, setInvites] = useState<Invite[] | null>(null)
  const [error, setError] = useState('')

  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('member')
  const [inviteLink, setInviteLink] = useState('')
  const [inviteErr, setInviteErr] = useState('')

  const load = useCallback(async () => {
    try {
      const [meR, mR, iR] = await Promise.all([
        apiFetch('/api/me'), apiFetch('/api/org/members'), apiFetch('/api/org/invitations'),
      ])
      if (meR.ok) setMe(await meR.json())
      if (mR.ok) setMembers((await mR.json()).members)
      else setError(`Failed to load members (HTTP ${mR.status})`)
      if (iR.ok) setInvites((await iR.json()).invitations)
    } catch (e) {
      setError(String((e as Error).message ?? e))
    }
  }, [apiFetch])

  useEffect(() => { if (ready) load() }, [ready, load])

  const myRank = me ? rankOf(me) : 0
  const canManage = (m: Member) => !!me && !m.isSuperAdmin && m.id !== me.id && rankOf(m) < myRank
  const grantableRoles = myRank >= RANK.owner ? ['member', 'admin'] : ['member']

  async function patchMember(m: Member, payload: object) {
    await apiFetch(`/api/org/members/${m.id}`, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    load()
  }

  async function sendInvite(e: React.FormEvent) {
    e.preventDefault()
    setInviteErr(''); setInviteLink('')
    const r = await apiFetch('/api/org/invitations', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: inviteEmail, role: inviteRole }),
    })
    if (r.ok) {
      const d = await r.json()
      setInviteLink(`${window.location.origin}/invite/accept?token=${d.token}`)
      setInviteEmail('')
      load()
    } else {
      const d = await r.json().catch(() => ({}))
      setInviteErr(
        d.detail === 'already_member' ? 'That person is already a member.'
        : d.detail === 'only_owner_can_invite_admin' ? 'Only an owner can invite an admin.'
        : 'Could not send the invitation.')
    }
  }

  async function revoke(inv: Invite) {
    await apiFetch(`/api/org/invitations/${inv.id}`, { method: 'DELETE' })
    load()
  }

  return (
    <div>
      <Link href="/admin" className="text-sm text-brand-600 hover:underline">← Admin</Link>
      <h1 className="mt-4 text-2xl font-bold">Members</h1>
      <p className="mt-1 text-slate-500">Manage roles, access, and invitations for your organization.</p>

      {error && <p className="mt-6 text-sm text-red-600">{error}</p>}

      {/* Members table */}
      {members && (
        <ul className="mt-6 divide-y divide-slate-200 overflow-hidden rounded-lg border border-slate-200 bg-white">
          {members.map((m) => (
            <li key={m.id} className="flex items-center justify-between gap-4 px-5 py-3">
              <div className="min-w-0">
                <p className="truncate font-medium text-slate-900">
                  {m.fullName}{!m.isActive && <span className="ml-2 text-xs text-red-600">(disabled)</span>}
                </p>
                <p className="truncate text-sm text-slate-500">{m.email}</p>
              </div>
              <div className="flex shrink-0 items-center gap-3">
                {canManage(m) ? (
                  <select
                    value={m.role}
                    onChange={(e) => patchMember(m, { role: e.target.value })}
                    className="rounded-md border border-slate-300 px-2 py-1 text-sm"
                  >
                    {[m.role, ...grantableRoles].filter((r, i, a) => a.indexOf(r) === i).map((r) => (
                      <option key={r} value={r}>{r}</option>
                    ))}
                  </select>
                ) : (
                  <RoleBadge role={m.role} />
                )}
                {canManage(m) && (
                  <button
                    onClick={() => patchMember(m, { isActive: !m.isActive })}
                    className="rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100"
                  >
                    {m.isActive ? 'Deactivate' : 'Reactivate'}
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      {/* Invite form */}
      <section className="mt-10">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Invite a member</h2>
        <form onSubmit={sendInvite} className="mt-3 flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-white p-5">
          <div className="flex-1">
            <label className="block text-sm font-medium text-slate-700">Email</label>
            <input
              type="email" value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} required
              placeholder="teammate@company.com"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700">Role</label>
            <select
              value={inviteRole} onChange={(e) => setInviteRole(e.target.value)}
              className="mt-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
            >
              {grantableRoles.map((r) => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <button className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
            Send invite
          </button>
        </form>
        {inviteErr && <p className="mt-2 text-sm text-red-600">{inviteErr}</p>}
        {inviteLink && (
          <div className="mt-3 rounded-md bg-green-50 p-3 text-sm">
            <p className="font-medium text-green-800">Invite created. Share this link:</p>
            <code className="mt-1 block break-all text-green-900">{inviteLink}</code>
          </div>
        )}
      </section>

      {/* Pending invitations */}
      {invites && invites.length > 0 && (
        <section className="mt-10">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Pending invitations</h2>
          <ul className="mt-3 divide-y divide-slate-200 overflow-hidden rounded-lg border border-slate-200 bg-white">
            {invites.map((inv) => (
              <li key={inv.id} className="flex items-center justify-between px-5 py-3">
                <div>
                  <p className="font-medium text-slate-900">{inv.email}</p>
                  <p className="text-xs text-slate-500">role: {inv.role} · expires {inv.expiresAt.slice(0, 10)}</p>
                </div>
                <button
                  onClick={() => revoke(inv)}
                  className="rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium text-red-600 hover:bg-red-50"
                >
                  Revoke
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
