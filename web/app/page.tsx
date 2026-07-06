import Link from 'next/link'

function Icon({ path }: { path: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <path d={path} />
    </svg>
  )
}

function Check() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="mt-0.5 h-4 w-4 shrink-0 text-brand-600"
      aria-hidden="true"
    >
      <path d="M20 6L9 17l-5-5" />
    </svg>
  )
}

const FEATURES = [
  {
    title: 'Plan and prioritize',
    body: 'Boards, backlogs, and priorities that keep every project moving. Break work into tasks, assign owners, and see status at a glance.',
    icon: 'M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01',
  },
  {
    title: 'Real-time collaboration',
    body: 'Comments, activity feeds, and live updates keep your whole team in sync without the endless status meetings.',
    icon: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0 8 4 4 0 0 0 0-8z',
  },
  {
    title: 'Secure by design',
    body: 'SSO and SAML, SCIM provisioning, scoped API tokens, granular roles, and a full audit log. Enterprise controls, on by default.',
    icon: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z',
  },
  {
    title: 'Built for developers',
    body: 'A first-class REST API, personal access tokens, and signed webhooks so you can automate anything and integrate what you already use.',
    icon: 'M16 18l6-6-6-6M8 6l-6 6 6 6',
  },
]

const SECURITY = [
  ['SSO and SAML', 'Bring your own identity provider and enforce single sign-on across your organization.'],
  ['SCIM provisioning', 'Automatically sync users and deprovision access the moment someone leaves.'],
  ['Granular roles', 'Owner, admin, and member roles scoped per organization and per project.'],
  ['Scoped API tokens', 'Issue personal access tokens with least-privilege scopes and rotate them anytime.'],
  ['Signed webhooks', 'Every event is signed so your integrations can trust what they receive.'],
  ['Full audit log', 'Every action is recorded with actor, resource, and timestamp for compliance.'],
]

const TESTIMONIALS = [
  {
    quote: 'Prolane replaced three tools for us. Our engineers finally have one place for work, and our admins have the controls they need.',
    name: 'Alice Nguyen',
    role: 'VP Engineering, Northwind Systems',
  },
  {
    quote: 'The API and webhooks let us wire Prolane into our whole delivery pipeline in an afternoon. Rollout across the org was painless.',
    name: 'Bob Castellano',
    role: 'Head of Platform, Bluepeak Labs',
  },
  {
    quote: 'Audit logs and SCIM were table stakes for our security review. Prolane passed on day one.',
    name: 'Marcus Webb',
    role: 'CISO, Northwind Systems',
  },
]

function FooterCol({ heading, links }: { heading: string; links: [string, string][] }) {
  return (
    <div>
      <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">{heading}</h4>
      <ul className="mt-3 space-y-2 text-sm text-slate-600">
        {links.map(([label, href]) => (
          <li key={label}>
            {href.startsWith('/') ? (
              <Link href={href} className="hover:text-slate-900">{label}</Link>
            ) : (
              <a href={href} className="hover:text-slate-900">{label}</a>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <span className="text-lg font-bold text-brand-600">Prolane</span>
          <nav className="hidden items-center gap-8 text-sm font-medium text-slate-600 sm:flex">
            <a href="#features" className="hover:text-slate-900">Features</a>
            <a href="#security" className="hover:text-slate-900">Security</a>
            <Link href="/pricing" className="hover:text-slate-900">Pricing</Link>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/login" className="text-sm font-medium text-slate-700 hover:text-slate-900">
              Sign in
            </Link>
            <Link
              href="/register"
              className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
            >
              Get started
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <section className="border-b border-slate-200 bg-gradient-to-b from-slate-50 to-white">
          <div className="mx-auto max-w-3xl px-6 py-24 text-center">
            <span className="inline-block rounded-full border border-brand-100 bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700">
              The secure workspace for modern teams
            </span>
            <h1 className="mt-6 text-4xl font-bold tracking-tight text-slate-900 sm:text-6xl">
              Project management, without the chaos
            </h1>
            <p className="mx-auto mt-6 max-w-xl text-lg text-slate-600">
              Plan work, track tasks, and keep your whole organization moving - all in one secure,
              API-first workspace your engineers and your security team will both love.
            </p>
            <div className="mt-9 flex justify-center gap-3">
              <Link
                href="/register"
                className="rounded-md bg-brand-600 px-6 py-3 text-sm font-semibold text-white hover:bg-brand-700"
              >
                Start free
              </Link>
              <Link
                href="/login"
                className="rounded-md border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              >
                Sign in
              </Link>
            </div>
            <p className="mt-4 text-xs text-slate-400">No credit card required. Free for small teams.</p>
          </div>
        </section>

        <section className="border-b border-slate-200 py-10">
          <div className="mx-auto max-w-5xl px-6">
            <p className="text-center text-xs font-semibold uppercase tracking-wider text-slate-400">
              Trusted by fast-moving teams
            </p>
            <div className="mt-6 flex flex-wrap items-center justify-center gap-x-12 gap-y-4 text-lg font-semibold text-slate-400">
              <span>Northwind Systems</span>
              <span>Bluepeak Labs</span>
              <span>Meridian Freight</span>
              <span>Corva Health</span>
              <span>Lumen Retail</span>
            </div>
          </div>
        </section>

        <section id="features" className="py-20">
          <div className="mx-auto max-w-6xl px-6">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight text-slate-900">
                Everything your team needs to ship
              </h2>
              <p className="mt-4 text-slate-600">
                From the first task to the enterprise rollout, Prolane scales with you.
              </p>
            </div>
            <div className="mt-14 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
              {FEATURES.map((f) => (
                <div key={f.title} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                    <Icon path={f.icon} />
                  </div>
                  <h3 className="mt-4 text-base font-semibold text-slate-900">{f.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-slate-600">{f.body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="border-y border-slate-200 bg-slate-50 py-20">
          <div className="mx-auto grid max-w-6xl items-center gap-12 px-6 lg:grid-cols-2">
            <div>
              <h2 className="text-3xl font-bold tracking-tight text-slate-900">One workspace, end to end</h2>
              <p className="mt-4 text-slate-600">
                Projects, tasks, comments, attachments, billing, and provisioning live together, so
                nothing falls through the cracks between tools.
              </p>
              <ul className="mt-6 space-y-3 text-sm text-slate-700">
                <li className="flex gap-3"><Check /> Kanban boards and prioritized backlogs</li>
                <li className="flex gap-3"><Check /> Live activity feed and audit history</li>
                <li className="flex gap-3"><Check /> Multi-tenant organizations with roles</li>
                <li className="flex gap-3"><Check /> Attachments, webhooks, and a full REST API</li>
              </ul>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-2 shadow-lg">
              <div className="rounded-xl bg-slate-900 p-4">
                <div className="flex gap-1.5">
                  <span className="h-3 w-3 rounded-full bg-red-400" />
                  <span className="h-3 w-3 rounded-full bg-amber-400" />
                  <span className="h-3 w-3 rounded-full bg-green-400" />
                </div>
                <div className="mt-4 space-y-2">
                  <div className="h-3 w-2/3 rounded bg-slate-700" />
                  <div className="h-3 w-1/2 rounded bg-slate-700" />
                  <div className="h-24 rounded bg-slate-800" />
                  <div className="grid grid-cols-3 gap-2">
                    <div className="h-16 rounded bg-slate-800" />
                    <div className="h-16 rounded bg-slate-800" />
                    <div className="h-16 rounded bg-slate-800" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="security" className="py-20">
          <div className="mx-auto max-w-6xl px-6">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight text-slate-900">Enterprise security, standard</h2>
              <p className="mt-4 text-slate-600">
                The controls your security team asks for are built in - not a premium upsell.
              </p>
            </div>
            <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {SECURITY.map(([title, body]) => (
                <div key={title} className="rounded-xl border border-slate-200 p-5">
                  <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
                  <p className="mt-1.5 text-sm text-slate-600">{body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="border-t border-slate-200 bg-slate-50 py-20">
          <div className="mx-auto max-w-6xl px-6">
            <h2 className="text-center text-3xl font-bold tracking-tight text-slate-900">
              Loved by teams that ship
            </h2>
            <div className="mt-12 grid gap-6 lg:grid-cols-3">
              {TESTIMONIALS.map((t) => (
                <figure key={t.name} className="flex flex-col rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
                  <blockquote className="flex-1 text-sm leading-relaxed text-slate-700">{t.quote}</blockquote>
                  <figcaption className="mt-5">
                    <div className="text-sm font-semibold text-slate-900">{t.name}</div>
                    <div className="text-xs text-slate-500">{t.role}</div>
                  </figcaption>
                </figure>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-brand-600">
          <div className="mx-auto max-w-4xl px-6 py-16 text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white">Ready to get organized?</h2>
            <p className="mx-auto mt-3 max-w-xl text-brand-100">
              Start free today, or see how our plans scale with your team.
            </p>
            <div className="mt-8 flex justify-center gap-3">
              <Link
                href="/register"
                className="rounded-md bg-white px-6 py-3 text-sm font-semibold text-brand-700 hover:bg-brand-50"
              >
                Start free
              </Link>
              <Link
                href="/pricing"
                className="rounded-md border border-white/40 px-6 py-3 text-sm font-semibold text-white hover:bg-white/10"
              >
                View pricing
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-12">
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <span className="text-lg font-bold text-brand-600">Prolane</span>
              <p className="mt-3 max-w-xs text-sm text-slate-500">
                The secure workspace for modern teams.
              </p>
            </div>
            <FooterCol
              heading="Product"
              links={[['Features', '#features'], ['Security', '#security'], ['Pricing', '/pricing']]}
            />
            <FooterCol
              heading="Company"
              links={[['About', '#'], ['Careers', '#'], ['Contact', '#']]}
            />
            <FooterCol
              heading="Legal"
              links={[['Privacy', '#'], ['Terms', '#'], ['Status', '#']]}
            />
          </div>
          <div className="mt-10 border-t border-slate-100 pt-6 text-center text-xs text-slate-400">
            Copyright 2026 Prolane, Inc. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}
