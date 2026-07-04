import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { getSessionUser } from './lib/session'

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Build split: the /secure/* pages are the secure twins of the client-side
  // vulns - they exist for the LAB face (manual side-by-side verification). In
  // the CHALLENGE face (VF_LAB=0) they are hidden, so the deployed target leaks
  // no "here is the patched version" signal. (Unset/`1` = lab; only explicit `0`
  // hides them, matching the api's config.VF_LAB default.)
  if (pathname.startsWith('/secure/') && process.env.VF_LAB === '0') {
    return new NextResponse(null, { status: 404 })
  }

  // Public routes reachable without a session.
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
    return NextResponse.next()
  }

  const user = await getSessionUser(request)
  if (!user) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
