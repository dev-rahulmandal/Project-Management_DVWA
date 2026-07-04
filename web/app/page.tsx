import Link from 'next/link'

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <span className="text-lg font-bold text-brand-600">VulnForge</span>
          <Link
            href="/login"
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            Sign in
          </Link>
        </div>
      </header>

      <main className="mx-auto flex max-w-3xl flex-1 flex-col items-center justify-center px-6 text-center">
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          Project management for modern teams
        </h1>
        <p className="mt-4 max-w-xl text-lg text-slate-600">
          Plan work, track tasks, and keep your whole organization moving - all in
          one secure workspace.
        </p>
        <div className="mt-8 flex gap-3">
          <Link
            href="/register"
            className="rounded-md bg-brand-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-brand-700"
          >
            Get started
          </Link>
          <Link
            href="/login"
            className="rounded-md border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Sign in
          </Link>
        </div>
      </main>

      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-400">
        VulnForge - a deliberately vulnerable training app. Education only.
      </footer>
    </div>
  )
}
