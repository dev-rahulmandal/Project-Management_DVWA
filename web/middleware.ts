import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { getSessionUser } from './lib/session'

const API_ORIGIN = process.env.NEXT_PUBLIC_API_ORIGIN ?? 'http://localhost:8081'
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
  ].join('; ')
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

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
