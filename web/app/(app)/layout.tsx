import { redirect } from 'next/navigation'
import { getSessionUserFromCookies } from '@/lib/session'
import { ApiProvider } from '@/components/Providers'
import { Sidebar } from '@/components/shell/Sidebar'
import { Topbar } from '@/components/shell/Topbar'

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const user = await getSessionUserFromCookies()
  if (!user) redirect('/login')

  const isAdmin = user.isSuperAdmin || user.role === 'owner' || user.role === 'admin'

  return (
    <ApiProvider>
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar isAdmin={isAdmin} />
        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar email={user.email} role={user.role} />
          <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">{children}</main>
        </div>
      </div>
    </ApiProvider>
  )
}
