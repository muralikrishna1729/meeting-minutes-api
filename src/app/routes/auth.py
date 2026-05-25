import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status,Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.session import get_db
from app.models import User
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.dependencies import get_current_user, oauth2_scheme
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from app.config import settings
from datetime import datetime, timezone
from app.core.limiter import limiter

router = APIRouter(prefix="/auth", tags=["auth"])

redis = aioredis.from_url(settings.REDIS_URL)

@router.post("/register",status_code=status.HTTP_201_CREATED, response_model=TokenResponse)
async def create_user(request:RegisterRequest, db: AsyncSession = Depends(get_db))->TokenResponse:
    result =  await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    user = User(
        email= request.email, 
        hashed_password=hash_password(request.password),
        role = "user",
        is_active = True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/login",status_code=status.HTTP_200_OK,response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request:Request,body:LoginRequest , db:AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalars().first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request:RefreshRequest, db:AsyncSession=Depends(get_db)):
    payload = decode_token(request.refresh_token)
    if payload["type"] != "refresh": 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    user_id = payload["sub"]
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    result = await db.execute(select(User).where(User.id ==user_id))
    user = result.scalars().first() 
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token  # ← same token back
    )

@router.post("/logout")
@limiter.limit("5/minute")
async def logout(
    request:Request,
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
):
    payload = decode_token(token)
    user_id = payload["sub"]
    exp = payload["exp"]
    jti = payload["jti"]
    remaining_ttl = int(exp - datetime.now(tz=timezone.utc).timestamp())
    if remaining_ttl > 0:
        await redis.set(f"blacklist:{jti}", "1", ex=remaining_ttl)
    return {"message": "Logged out successfully"}



