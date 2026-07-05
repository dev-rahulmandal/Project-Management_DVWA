import { redirect } from 'next/navigation'
import { getSessionUserFromCookies } from '@/lib/session'

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const user = await getSessionUserFromCookies()
  if (!user) redirect('/login')

  const isAdmin = user.isSuperAdmin || user.role === 'owner' || user.role === 'admin'
  if (!isAdmin) redirect('/dashboard')

  return <>{children}</>
}
