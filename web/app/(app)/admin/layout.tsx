import { redirect } from 'next/navigation'
import { getSessionUserFromCookies } from '@/lib/session'

// Server-side guard for the admin area. This mirrors (but does not replace) the
// api's require_admin check - the api is the real boundary; this just keeps
// non-admins from rendering a page they can't use.
export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const user = await getSessionUserFromCookies()
  if (!user) redirect('/login')

  const isAdmin = user.isSuperAdmin || user.role === 'owner' || user.role === 'admin'
  if (!isAdmin) redirect('/dashboard')

  return <>{children}</>
}
