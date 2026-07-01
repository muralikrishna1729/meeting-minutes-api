from fastapi import APIRouter, Response, status
from sqlalchemy import text
from app.db.session import get_db
from app.core.cache import redis_client  
from app.config import settings
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
@router.get("/health", tags=["health"])
async def health_check(response:Response, db:AsyncSession= Depends(get_db)):
    db_status= "ok"
    redis_status = "ok"
    overall = "healthy"

    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unreachable"
        overall = "degraded"
    
    try:
        await redis_client.ping()
    except Exception:
        redis_status = "unreachable"
        overall = "degraded"
    
    if overall == "degraded":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status":  overall,
        'database': db_status,
        "redis": redis_status,
        "summarizer": settings.SUMMARIZER_TYPE
    }