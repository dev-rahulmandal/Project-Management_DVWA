import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Prolane',
  description: 'Project management for modern teams.',
}

export const dynamic = 'force-dynamic'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
