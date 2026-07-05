import { NextRequest, NextResponse } from 'next/server'
import { createSessionToken, SESSION_COOKIE } from '@/lib/session'

export async function POST(request: NextRequest) {
  const origin     = request.headers.get('origin')
  const xrw        = request.headers.get('x-requested-with')
  const csrfHeader = request.headers.get('x-csrf-token')
  const csrfCookie = request.cookies.get('vf_csrf')?.value
  const allowedOrigins = (process.env.WEB_ORIGIN ?? 'http://localhost:8082')
    .split(',').map((o) => o.trim()).filter(Boolean)

  if (xrw !== 'fetch')
    return NextResponse.json({ error: 'missing_xrw' }, { status: 400 })
  if (!origin || !allowedOrigins.includes(origin))
    return NextResponse.json({ error: 'bad_origin' }, { status: 403 })
  if (!csrfHeader || !csrfCookie || csrfHeader !== csrfCookie)
    return NextResponse.json({ error: 'csrf_mismatch' }, { status: 403 })

  let body: { token?: string; fullName?: string; password?: string }
  try { body = await request.json() } catch { body = {} }
  const { token, fullName, password } = body
  if (!token || !fullName || !password)
    return NextResponse.json({ error: 'missing_fields' }, { status: 400 })

  const apiOrigin = process.env.INTERNAL_API_ORIGIN ?? 'http://localhost:8081'
  const res = await fetch(`${apiOrigin}/api/internal/accept-invite`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token, fullName, password }),
  })

  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    return NextResponse.json({ error: detail.detail ?? 'accept_failed' },
      { status: res.status === 409 ? 409 : 400 })
  }

  const user = await res.json()

  const session = await createSessionToken({
    id:           user.id,
    email:        user.email,
    orgId:        user.orgId,
    role:         user.role,
    isSuperAdmin: user.isSuperAdmin,
  })

  const out = NextResponse.json({ ok: true })
  out.cookies.set(SESSION_COOKIE, session, {
    httpOnly: true, sameSite: 'lax', path: '/', maxAge: 60 * 60 * 24,
  })
  out.cookies.delete('vf_csrf')
  return out
}
