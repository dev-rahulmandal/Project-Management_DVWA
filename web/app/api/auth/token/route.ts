import { NextRequest, NextResponse } from 'next/server'
import { getSessionUser } from '@/lib/session'
import { mintApiToken } from '@/lib/auth'

export async function POST(request: NextRequest) {
  const user = await getSessionUser(request)
  if (!user) return NextResponse.json({ error: 'no_session' }, { status: 401 })

  const token = await mintApiToken(user)
  return NextResponse.json({ token })
}
