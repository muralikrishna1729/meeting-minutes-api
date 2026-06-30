from datetime import datetime, timedelta, timezone
from uuid import uuid4
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.config import settings


SECRET_KEY      = settings.SECRET_KEY
ALGORITHM       = "HS256"           # signing algorithm
ACCESS_EXPIRE   = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_EXPIRE = settings.REFRESH_TOKEN_EXPIRE_DAYS


pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain_password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_ctx.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hashed password."""
    return pwd_ctx.verify(plain_password,hashed_password)

def create_access_token(user_id:str) -> str:
    payload = {
        "sub":user_id,
        "type":'access',
        "jti": str(uuid4()),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRE),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)

def create_refresh_token(user_id:str) -> str:
    payload = {
        "sub":user_id,
        "type":'refresh',
        "jti": str(uuid4()),
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRE),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGORITHM)

def decode_token(token:str) -> dict:
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token",headers={"WWW-Authenticate": "Bearer"})