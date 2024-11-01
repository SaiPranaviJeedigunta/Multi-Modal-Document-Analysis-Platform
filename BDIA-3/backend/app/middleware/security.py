from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer
from ..services.auth_service import AuthService
import jwt

security = HTTPBearer()
auth_service = AuthService()

async def verify_token(request: Request):
    """Verify JWT token and add user to request state"""
    try:
        auth = await security(request)
        token = auth.credentials
        user = await auth_service.get_current_user(token)
        request.state.user = user
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )