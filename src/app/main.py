import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes.auth import router as auth_router
from app.routes.minutes import router as minutes_router
from app.routes.admin import router as admin_router
from app.core.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"    
)
logger = logging.getLogger(__name__)
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="API for transcribing and summarizing meeting minutes"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = ["*"],
    allow_credentials = True,
    allow_headers = ["*"],
)
app.include_router(auth_router, prefix= "/api/v1")
app.include_router(minutes_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")

    
@app.on_event("startup")
async def startup_event():
    """Log application startup"""
    logger.info(f"Application {settings.APP_NAME} started successfully")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Summarizer type: {settings.SUMMARIZER_TYPE}")


@app.get("/health", tags= ["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV
    }

@app.get("/",tags= ['root'])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Meeting Minutes API",
        "version": "1.0.0",
        "docs": "/docs"
    }
 