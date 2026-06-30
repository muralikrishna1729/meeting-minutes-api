from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.APP_ENV == "development",
    pool_size=10,
    max_overflow=20
)

AsyncSessionLocal = async_sessionmaker(engine , expire_on_commit=False, class_=AsyncSession)

async def get_db():
    """Get a database session."""
    async with AsyncSessionLocal() as db:
        yield db
    


