import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

PRIVATE_PEM = _key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
).decode()

_public = _key.public_key()
PUBLIC_PEM = _public.public_bytes(
    serialization.Encoding.PEM,
    serialization.PublicFormat.SubjectPublicKeyInfo,
).decode()

KID = "vf-oauth-rs256-1"


def _b64u(n: int) -> str:
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


_nums = _public.public_numbers()
JWKS = {"keys": [{
    "kty": "RSA", "use": "sig", "alg": "RS256", "kid": KID,
    "n": _b64u(_nums.n), "e": _b64u(_nums.e),
}]}
