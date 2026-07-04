import { NextRequest, NextResponse } from 'next/server'
import { getSessionUser } from '@/lib/session'
import { mintApiToken } from '@/lib/auth'

// Exchanges a valid session cookie for an API Bearer token.
// This is what gives the browser (and the scanner) its credential for the api origin.
export async function POST(request: NextRequest) {
  const user = await getSessionUser(request)
  if (!user) return NextResponse.json({ error: 'no_session' }, { status: 401 })

  const token = await mintApiToken(user)
  return NextResponse.json({ token })
}
