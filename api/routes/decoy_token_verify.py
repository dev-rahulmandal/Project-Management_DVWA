import jwt
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

_INTEGRATION_SECRET = "il1Xp9Q2rZ7mB4nK6tW8vF0dS3gY5jL_prolane_integrations_hs256"


class VerifyToken(BaseModel):
    token: str


@router.post("/api/integrations/verify-token")
async def verify_token(body: VerifyToken):
    try:
        claims = jwt.decode(body.token, _INTEGRATION_SECRET, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401, detail="invalid_token")
    return {"verified": True, "claims": claims}
