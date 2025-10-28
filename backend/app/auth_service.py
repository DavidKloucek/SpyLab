from wireup import service
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from app.app_config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    PRIVATE_KEY_PATH,
    PUBLIC_KEY_PATH,
)
from app.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class TokenPayload(BaseModel):
    sub: int
    email: str
    exp: int


@service(lifetime="scoped")
class AuthService:
    def __init__(self):
        self._loaded = False
        self.private_key = None
        self.public_key = None

    def _load_scheme(self):
        with open(PRIVATE_KEY_PATH, "r") as f:
            self.private_key = f.read()

        with open(PUBLIC_KEY_PATH, "r") as f:
            self.public_key = f.read()

        self._loaded = True

    def create_access_token(self, user: User):
        if not self._loaded:
            self._load_scheme()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": str(user.id),
            "email": user.email,
            "exp": expire,
        }
        return jwt.encode(to_encode, self.private_key, algorithm=ALGORITHM)

    def decode_access_token(self, token: str) -> TokenPayload:
        if not self._loaded:
            self._load_scheme()
        try:
            payload = jwt.decode(token, self.public_key, algorithms=[ALGORITHM])
            return TokenPayload(**payload)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
