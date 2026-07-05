import { SignJWT } from 'jose'
import type { SessionUser } from './session'

const JWT_SECRET = new TextEncoder().encode(process.env.JWT_SECRET ?? 'summer2023')
const JWT_ISSUER = process.env.JWT_ISSUER ?? 'prolane-api'

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
