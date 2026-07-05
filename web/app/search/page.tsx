'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import Link from 'next/link'

type Article = { title: string; category: string; excerpt: string; body: string }

const CATEGORIES = [
  'Getting started',
  'Projects and tasks',
  'Billing and plans',
  'Security',
  'API and webhooks',
  'Account',
]

const ARTICLES: Article[] = [
  {
    title: 'Create your first workspace',
    category: 'Getting started',
    excerpt: 'Spin up a workspace and invite your team in under a minute.',
    body: 'A workspace is the home for your organization. When you register you get one automatically. From Settings you can rename it, set a slug, and manage members.',
  },
  {
    title: 'Invite your team',
    category: 'Getting started',
    excerpt: 'Send invitations by email and assign roles.',
    body: 'Open Members, enter an email, pick a role (member, admin, or owner), and send. Invitees receive a link that lets them set a name and password.',
  },
  {
    title: 'Set up your first project',
    category: 'Getting started',
    excerpt: 'Group related work into a project with tasks and files.',
    body: 'Projects hold tasks, comments, and file attachments. Create one from the Projects page, then add tasks and drag them across the board as work progresses.',
  },
  {
    title: 'Organize work with projects',
    category: 'Projects and tasks',
    excerpt: 'Use projects to separate initiatives and control access.',
    body: 'Each project is scoped to your organization. Archive a project to hide it from the active list without deleting its history; restore it any time.',
  },
  {
    title: 'Using the Kanban board',
    category: 'Projects and tasks',
    excerpt: 'Move tasks through Open, In Progress, and Done.',
    body: 'The board groups tasks by status. Click the move control on a card to advance it, or open a task to edit its title, assignee, priority, and due date.',
  },
  {
    title: 'Labels, priorities, and due dates',
    category: 'Projects and tasks',
    excerpt: 'Add structure so the right work surfaces first.',
    body: 'Apply colored labels to categorize tasks, set a priority from low to high, and add a due date. Filter the board by any of these from the task list.',
  },
  {
    title: 'Comment and mention teammates',
    category: 'Projects and tasks',
    excerpt: 'Discuss work in context on each task.',
    body: 'Every task has a comment thread. Mentioning a teammate notifies them and adds the task to their notifications center.',
  },
  {
    title: 'Understand your plan and usage',
    category: 'Billing and plans',
    excerpt: 'See your current plan, seats, and credit balance.',
    body: 'The Billing page shows your plan tier, seats in use, and remaining credits. Usage that exceeds your plan prompts an upgrade.',
  },
  {
    title: 'Upgrade or downgrade your plan',
    category: 'Billing and plans',
    excerpt: 'Change plans at any time with prorated billing.',
    body: 'Pick a new plan from Billing. Upgrades take effect immediately; downgrades apply at the end of the current cycle. Charges are prorated to the day.',
  },
  {
    title: 'Apply a coupon or credit',
    category: 'Billing and plans',
    excerpt: 'Redeem a promo code or use account credits at checkout.',
    body: 'Enter a coupon code on the Billing page to apply a discount. Account credits from refunds or credit packs are used automatically on your next charge.',
  },
  {
    title: 'Request a refund',
    category: 'Billing and plans',
    excerpt: 'Paid plans include a 30-day money-back guarantee.',
    body: 'Contact support within 30 days of a charge and we will credit your account. Refunds are issued as account credit or back to the original payment method.',
  },
  {
    title: 'Reset your password',
    category: 'Security',
    excerpt: 'Recover access if you forget your password.',
    body: 'Use the password reset link on the sign-in page. You will receive a one-time link by email that lets you choose a new password.',
  },
  {
    title: 'Enable single sign-on (SSO)',
    category: 'Security',
    excerpt: 'Connect your identity provider on Enterprise plans.',
    body: 'Enterprise organizations can enable SAML SSO and SCIM provisioning so members sign in through your IdP and are provisioned automatically.',
  },
  {
    title: 'Review your audit log',
    category: 'Security',
    excerpt: 'Track who did what across your organization.',
    body: 'Admins can review the audit log to see project, task, and settings changes with the actor and timestamp for each event.',
  },
  {
    title: 'Create a personal access token',
    category: 'API and webhooks',
    excerpt: 'Authenticate scripts and integrations with a scoped token.',
    body: 'Generate a personal access token from the Developer page, choose its scopes, and use it as a bearer token against the API. The token is shown only once.',
  },
  {
    title: 'Register an outbound webhook',
    category: 'API and webhooks',
    excerpt: 'Receive signed event callbacks at your endpoint.',
    body: 'Add a webhook URL and select the events you care about. Each delivery is signed so your endpoint can verify it came from Prolane.',
  },
  {
    title: 'Update your profile',
    category: 'Account',
    excerpt: 'Change your name, email, and password.',
    body: 'Open Settings to edit your display name and email or change your password. Your role and organization are shown for reference.',
  },
  {
    title: 'Manage notifications',
    category: 'Account',
    excerpt: 'Stay on top of mentions, assignments, and comments.',
    body: 'The notifications center collects mentions, task assignments, and new comments. Mark items read individually or clear them all at once.',
  },
]

export default function SearchPage() {
  const resultRef = useRef<HTMLDivElement>(null)
  const [term, setTerm] = useState('')
  const [query, setQuery] = useState('')

  useEffect(() => {
    const render = () => {
      let q = ''
      try {
        q = decodeURIComponent(window.location.hash.slice(1))
      } catch {
        q = window.location.hash.slice(1)
      }
      setQuery(q)
      setTerm(q)
      if (resultRef.current) {
        resultRef.current.innerHTML = q ? `Showing results for: <strong>${q}</strong>` : ''
      }
    }
    render()
    window.addEventListener('hashchange', render)
    return () => window.removeEventListener('hashchange', render)
  }, [])

  const results = useMemo(() => {
    const needle = query.trim().toLowerCase()
    if (!needle) return []
    return ARTICLES.filter(
      (a) =>
        a.title.toLowerCase().includes(needle) ||
        a.excerpt.toLowerCase().includes(needle) ||
        a.category.toLowerCase().includes(needle),
    )
  }, [query])

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    window.location.hash = encodeURIComponent(term)
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <Link href="/" className="text-lg font-bold text-brand-600">Prolane</Link>
          <nav className="flex items-center gap-4 text-sm">
            <Link href="/pricing" className="text-slate-600 hover:text-slate-900">Pricing</Link>
            <Link href="/login" className="text-slate-600 hover:text-slate-900">Sign in</Link>
          </nav>
        </div>
      </header>

      <div className="bg-white">
        <div className="mx-auto max-w-3xl px-6 py-14 text-center">
          <h1 className="text-3xl font-bold text-slate-900">How can we help?</h1>
          <p className="mt-2 text-slate-600">
            Search the help center or browse articles by topic.
          </p>
          <form onSubmit={submit} className="mx-auto mt-6 flex max-w-xl gap-2">
            <input
              value={term}
              onChange={(e) => setTerm(e.target.value)}
              placeholder="Search articles"
              className="flex-1 rounded-md border border-slate-300 px-4 py-2.5 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
            <button className="rounded-md bg-brand-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-brand-700">
              Search
            </button>
          </form>
        </div>
      </div>

      <main className="mx-auto max-w-5xl px-6 py-12">
        <div ref={resultRef} className="text-lg text-slate-700" />

        {query ? (
          <div className="mt-6">
            {results.length > 0 ? (
              <ul className="space-y-3">
                {results.map((a) => (
                  <li key={a.title} className="rounded-lg border border-slate-200 bg-white p-4">
                    <p className="text-xs font-medium uppercase tracking-wide text-brand-600">
                      {a.category}
                    </p>
                    <h3 className="mt-1 font-semibold text-slate-900">{a.title}</h3>
                    <p className="mt-1 text-sm text-slate-600">{a.excerpt}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 text-sm text-slate-500">
                No articles match your search. Try a different term or browse by topic below.
              </p>
            )}
          </div>
        ) : (
          <div className="space-y-10">
            {CATEGORIES.map((cat) => {
              const items = ARTICLES.filter((a) => a.category === cat)
              return (
                <section key={cat}>
                  <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                    {cat}
                  </h2>
                  <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
                    {items.map((a) => (
                      <div key={a.title} className="rounded-lg border border-slate-200 bg-white p-4">
                        <h3 className="font-semibold text-slate-900">{a.title}</h3>
                        <p className="mt-1 text-sm text-slate-600">{a.excerpt}</p>
                        <p className="mt-2 text-sm text-slate-500">{a.body}</p>
                      </div>
                    ))}
                  </div>
                </section>
              )
            })}
          </div>
        )}
      </main>

      <footer className="border-t border-slate-200 bg-white py-8 text-center text-xs text-slate-400">
        Copyright 2026 Prolane, Inc. All rights reserved.
      </footer>
    </div>
  )
}
