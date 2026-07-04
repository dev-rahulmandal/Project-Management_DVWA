import { SignJWT, jwtVerify } from 'jose'
import { cookies } from 'next/headers'
import type { NextRequest } from 'next/server'

export const SESSION_COOKIE = 'vf_session'

const secret = new TextEncoder().encode(
  process.env.SESSION_SECRET ?? 'fake-session-secret-for-training-only'
)

export interface SessionUser {
  id: number
  email: string
  orgId: number
  role: string
  isSuperAdmin: boolean
}

export async function createSessionToken(user: SessionUser): Promise<string> {
  return new SignJWT({ ...user })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('24h')
    .sign(secret)
}

// For middleware (Edge runtime) - reads from the incoming request
export async function getSessionUser(req: NextRequest): Promise<SessionUser | null> {
  const token = req.cookies.get(SESSION_COOKIE)?.value
  if (!token) return null
  try {
    const { payload } = await jwtVerify(token, secret)
    return payload as unknown as SessionUser
  } catch {
    return null
  }
}

// For Server Components and Route Handlers (Node runtime) - reads from cookie store
export async function getSessionUserFromCookies(): Promise<SessionUser | null> {
  const store = cookies()
  const token = store.get(SESSION_COOKIE)?.value
  if (!token) return null
  try {
    const { payload } = await jwtVerify(token, secret)
    return payload as unknown as SessionUser
  } catch {
    return null
  }
}
