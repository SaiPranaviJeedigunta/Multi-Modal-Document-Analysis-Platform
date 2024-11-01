from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import JWTError, jwt
from ..models.auth import Token, TokenData, User
from ..services.auth_service import AuthService
from app.config.settings import Settings

router = APIRouter()
auth_service = AuthService()
settings = Settings()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    access_token = auth_service.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    return current_user