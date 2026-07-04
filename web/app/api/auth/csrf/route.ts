import { NextResponse } from 'next/server'
import { randomBytes } from 'crypto'

export async function GET() {
  const token = randomBytes(24).toString('hex')

  const res = NextResponse.json({ csrfToken: token })
  // Readable by JS (double-submit pattern) - intentionally not httpOnly
  res.cookies.set('vf_csrf', token, { httpOnly: false, sameSite: 'strict', path: '/' })
  return res
}
