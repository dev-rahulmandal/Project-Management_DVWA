import { NextRequest, NextResponse } from 'next/server'
import { createSessionToken, SESSION_COOKIE } from '@/lib/session'

export async function POST(request: NextRequest) {
  // ── Browser-required checks (same posture as login) ──────────────────────
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

  // ── Fields ────────────────────────────────────────────────────────────────
  let body: { email?: string; password?: string; fullName?: string; orgName?: string }
  try { body = await request.json() } catch { body = {} }
  const { email, password, fullName, orgName } = body
  if (!email || !password || !fullName || !orgName)
    return NextResponse.json({ error: 'missing_fields' }, { status: 400 })

  // ── Create the org + owner via the api service (BFF - web owns no DB) ─────
  // Only these four fields are forwarded; role/super-admin are decided server-side.
  const apiOrigin = process.env.INTERNAL_API_ORIGIN ?? 'http://localhost:8081'
  const regRes = await fetch(`${apiOrigin}/api/internal/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, fullName, orgName }),
  })

  if (!regRes.ok) {
    const detail = await regRes.json().catch(() => ({}))
    const status = regRes.status === 409 ? 409 : 400
    return NextResponse.json({ error: detail.detail ?? 'registration_failed' }, { status })
  }

  const user = await regRes.json()

  // ── Auto-login: issue the session cookie, same as the login route ─────────
  const token = await createSessionToken({
    id:           user.id,
    email:        user.email,
    orgId:        user.orgId,
    role:         user.role,
    isSuperAdmin: user.isSuperAdmin,
  })

  const res = NextResponse.json({ ok: true })
  res.cookies.set(SESSION_COOKIE, token, {
    httpOnly: true,
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 24,
  })
  res.cookies.delete('vf_csrf')
  return res
}
