from fastapi import Depends, HTTPException, status
from wireup import service
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from app import app_config as cfg
from app.user import User
import bcrypt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class TokenPayload(BaseModel):
    sub: int
    email: EmailStr
    exp: int


@service(lifetime="scoped")
class AuthService:
    @staticmethod
    def verify_password(plain: str, hash: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hash.encode())

    @staticmethod
    def create_access_token(user: User):
        expire = datetime.utcnow() + timedelta(minutes=cfg.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": str(user.id),
            "email": user.email,
            "exp": expire,
        }
        private_key = open(cfg.PRIVATE_KEY_PATH, "r").read()
        return jwt.encode(to_encode, private_key, algorithm=cfg.ALGORITHM)

    @staticmethod
    def decode_access_token(token: str) -> TokenPayload:
        public_key = open(cfg.PUBLIC_KEY_PATH, "r").read()
        payload = jwt.decode(token, public_key, algorithms=[cfg.ALGORITHM])
        return TokenPayload(**payload)


def fastapi_require_access_token(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    try:
        return AuthService.decode_access_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
