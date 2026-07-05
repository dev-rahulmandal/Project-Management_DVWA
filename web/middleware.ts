import { NextResponse } from 'next/server'
import type { NextRequest, NextFetchEvent } from 'next/server'
import { getSessionUser } from './lib/session'

const API_ORIGIN = process.env.NEXT_PUBLIC_API_ORIGIN ?? 'http://localhost:8081'
const REPORT_ENDPOINT = `${API_ORIGIN}/api/telemetry/csp`
const INTERNAL_API = process.env.INTERNAL_API_ORIGIN ?? 'http://localhost:8081'
const CLIENT_EVENT_ENDPOINT = `${INTERNAL_API}/api/telemetry/client`
const IS_DEV = process.env.NODE_ENV !== 'production'

function buildCsp(nonce: string): string {
  return [
    `default-src 'self'`,
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${IS_DEV ? " 'unsafe-eval'" : ''}`,
    `style-src 'self' 'unsafe-inline'`,
    `img-src 'self' data: blob:`,
    `font-src 'self'`,
    `connect-src 'self' ${API_ORIGIN}`,
    `object-src 'none'`,
    `base-uri 'self'`,
    `form-action 'self'`,
    `frame-ancestors 'none'`,
    `report-uri ${REPORT_ENDPOINT}`,
  ].join('; ')
}

function beacon(event: NextFetchEvent, kind: string) {
  event.waitUntil(
    fetch(CLIENT_EVENT_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body: JSON.stringify({ t: kind }),
    }).catch(() => {}),
  )
}

export async function middleware(request: NextRequest, event: NextFetchEvent) {
  const { pathname } = request.nextUrl

  if (pathname === '/customize') {
    const cfg = request.nextUrl.searchParams.get('config') || ''
    if (/__proto__|constructor|prototype/.test(cfg)) beacon(event, 'proto')
  }

  const isPrefetch =
    request.headers.has('next-router-prefetch') || request.headers.get('purpose') === 'prefetch'
  const isRsc = request.headers.has('rsc')
  const isDocument = !pathname.startsWith('/api') && !isPrefetch && !isRsc

  const nonce = isDocument ? btoa(crypto.randomUUID()) : ''
  const csp = isDocument ? buildCsp(nonce) : ''

  const requestHeaders = new Headers(request.headers)
  if (isDocument) {
    requestHeaders.set('x-nonce', nonce)
    requestHeaders.set('Content-Security-Policy', csp)
  }
  const nextOpts = isDocument ? { request: { headers: requestHeaders } } : undefined

  const withCsp = (res: NextResponse): NextResponse => {
    if (isDocument) res.headers.set('Content-Security-Policy-Report-Only', csp)
    return res
  }

  if (pathname.startsWith('/secure/') && process.env.VF_LAB !== '1') {
    return new NextResponse(null, { status: 404 })
  }

  if (
    pathname === '/' ||
    pathname.startsWith('/login') ||
    pathname.startsWith('/register') ||
    pathname.startsWith('/search') ||
    pathname.startsWith('/secure/search') ||
    pathname.startsWith('/pricing') ||
    pathname.startsWith('/secure/pricing') ||
    pathname.startsWith('/customize') ||
    pathname.startsWith('/secure/customize') ||
    pathname.startsWith('/embed') ||
    pathname.startsWith('/secure/embed') ||
    pathname.startsWith('/invite') ||
    pathname.startsWith('/api/auth')
  ) {
    return withCsp(NextResponse.next(nextOpts))
  }

  const user = await getSessionUser(request)
  if (!user) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  return withCsp(NextResponse.next(nextOpts))
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
