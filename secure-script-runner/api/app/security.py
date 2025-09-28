from fastapi import Header, HTTPException, Request
from typing import Optional
from app.config import settings
from jose import jwt
import httpx

class Principal:
    def __init__(self, user_email: str, role: str = "user", user_id: Optional[int] = None):
        self.email = user_email
        self.role = role
        self.user_id = user_id

async def get_principal(request: Request, x_demo_user: Optional[str] = Header(None)) -> Principal:
    if settings.AUTH_MODE == 'demo_header':
        if not x_demo_user:
            raise HTTPException(status_code=401, detail="Missing X-Demo-User header in demo mode")
        # role will be resolved from DB later
        return Principal(user_email=x_demo_user)
    elif settings.AUTH_MODE == 'oidc':
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Bearer token required")
        token = auth.split(' ', 1)[1]
        if not settings.OIDC_JWKS_URL or not settings.OIDC_AUDIENCE or not settings.OIDC_ISSUER:
            raise HTTPException(status_code=500, detail="OIDC not configured")
        # Stateless verification using JWKS
        async with httpx.AsyncClient() as client:
            jwks = (await client.get(settings.OIDC_JWKS_URL)).json()
        try:
            claims = jwt.get_unverified_claims(token)
            kid = jwt.get_unverified_header(token).get('kid')
            key = None
            for k in jwks.get('keys', []):
                if k.get('kid') == kid:
                    key = k
                    break
            if not key:
                raise HTTPException(status_code=401, detail="JWKS key not found")
            jwt.decode(
                token,
                key,
                audience=settings.OIDC_AUDIENCE,
                issuer=settings.OIDC_ISSUER,
                options={"verify_at_hash": False},
            )
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
        email = claims.get('preferred_username') or claims.get('upn') or claims.get('email')
        if not email:
            raise HTTPException(status_code=401, detail="Token missing email claim")
        return Principal(user_email=email)
    else:
        raise HTTPException(status_code=500, detail="Unknown AUTH_MODE")
