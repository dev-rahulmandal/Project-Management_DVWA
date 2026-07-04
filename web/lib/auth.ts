import { SignJWT } from 'jose'
import type { SessionUser } from './session'

const JWT_SECRET = new TextEncoder().encode(process.env.JWT_SECRET ?? 'changeme')
const JWT_ISSUER = process.env.JWT_ISSUER ?? 'vulnforge-api'

// Mints the Bearer token the browser hands to the api origin.
// Must match what api/auth.py expects: HS256, iss=vulnforge-api, sub=string user id.
export async function mintApiToken(user: SessionUser): Promise<string> {
  return new SignJWT({
    sub: String(user.id),
    email: user.email,
    role: user.role,
    org_id: user.orgId,
    is_super_admin: user.isSuperAdmin,
  })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuer(JWT_ISSUER)
    .setIssuedAt()
    .setExpirationTime('1h')
    .sign(JWT_SECRET)
}
