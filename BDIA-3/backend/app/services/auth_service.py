from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.models.auth import TokenData, User
from app.config.settings import Settings  # Updated import path

class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.settings = Settings()
        # Mock user database - replace with actual database in production
        self.users_db = {
            "test@example.com": {
                "username": "test@example.com",
                "full_name": "Test User",
                "email": "test@example.com",
                "hashed_password": self.get_password_hash("password123"),
                "disabled": False,
            }
        }

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against a hashed password."""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Generate a hash from a plain password."""
        return self.pwd_context.hash(password)

    def get_user(self, username: str) -> Optional[User]:
        """Get user from database."""
        if username in self.users_db:
            user_dict = self.users_db[username]
            return User(**user_dict)
        return None

    def authenticate_user(self, username: str, password: str) -> User:
        """Authenticate a user."""
        user = self.get_user(username)
        if not user:
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        if not self.verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        return user

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create an access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, 
            self.settings.SECRET_KEY, 
            algorithm=self.settings.ALGORITHM
        )
        return encoded_jwt

    async def get_current_user(self, token: str) -> User:
        """Get the current user from a token."""
        credentials_exception = HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(
                token, 
                self.settings.SECRET_KEY, 
                algorithms=[self.settings.ALGORITHM]
            )
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except JWTError:
            raise credentials_exception
            
        user = self.get_user(username=token_data.username)
        if user is None:
            raise credentials_exception
        return user

    async def get_current_active_user(self, token: str) -> User:
        """Get the current active user."""
        current_user = await self.get_current_user(token)
        if current_user.disabled:
            raise HTTPException(status_code=400, detail="Inactive user")
        return current_user