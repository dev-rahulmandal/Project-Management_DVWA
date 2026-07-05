import Link from 'next/link'

export default function SecureEmbedPage() {
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
