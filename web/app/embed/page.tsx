import Link from 'next/link'

// WEB-CLICKJACK-001: this sensitive-action page sets no X-Frame-Options or CSP
// frame-ancestors, so an attacker can load it in a transparent iframe and trick
// a logged-in victim into clicking the destructive button (UI redressing).
// The secured twin /secure/embed is frame-protected via next.config headers().
export default function EmbedPage() {
  return (
    <div className="mx-auto max-w-md px-6 py-16 text-center">
      <Link href="/" className="text-sm text-brand-600 hover:underline">← Home</Link>
      <h1 className="mt-6 text-2xl font-bold text-red-700">Confirm workspace deletion</h1>
      <p className="mt-2 text-slate-600">
        This permanently deletes your workspace and every project in it.
      </p>
      <button className="mt-6 rounded-md bg-red-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-red-700">
        Yes, delete everything
      </button>
    </div>
  )
}
