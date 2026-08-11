import os
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.db.session import get_db
from app.models import Base
from app.config import settings
from app.constants import MEETINGS_COLLECTION, TASKS_COLLECTION

# Point tests at a reachable MongoDB.  Default to localhost for the WSL venv;
# override with MONGODB_URL when running inside a container (e.g. host.docker.internal).
TEST_MONGODB_URL = os.environ.get("MONGODB_URL", "mongodb://localhost:27017")

# --- Postgres/SQLite (for auth — User table) ---
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# --- MongoDB (for meetings/tasks) ---
# Routes use app.db.mongo.db — a module-level AsyncIOMotorClient bound to the
# loop at import.  pytest-asyncio gives each test a FRESH loop, so the module
# client is bound to a dead loop → motor's run_in_executor fails.  Recreate the
# app's mongo client per test so it binds to the test's loop, and clean between
# tests with sync pymongo (no loop needed).
import pymongo
import motor.motor_asyncio
import app.db.mongo as app_mongo

@pytest_asyncio.fixture(autouse=True)
async def clean_mongo():
    # recreate the module-level client so motor binds to this test's loop
    app_mongo.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(TEST_MONGODB_URL)
    app_mongo.db = app_mongo.mongo_client[settings.MONGODB_DB]
    fresh_meetings = app_mongo.db[MEETINGS_COLLECTION]
    fresh_tasks = app_mongo.db[TASKS_COLLECTION]
    # routes/worker captured collections at import from the OLD client — patch
    # them to the fresh ones bound to this test's loop
    with patch("app.routes.minutes.meetings", fresh_meetings), \
         patch("app.routes.minutes.tasks", fresh_tasks), \
         patch("app.tasks.summarize.meetings", fresh_meetings), \
         patch("app.tasks.summarize.tasks", fresh_tasks):
        client = pymongo.MongoClient(TEST_MONGODB_URL)
        test_db = client[settings.MONGODB_DB]
        test_db[MEETINGS_COLLECTION].delete_many({})
        test_db[TASKS_COLLECTION].delete_many({})
        yield
        test_db[MEETINGS_COLLECTION].delete_many({})
        test_db[TASKS_COLLECTION].delete_many({})

# --- Mocks (unchanged) ---
# mock_redis, mock_celery, async_client, auth_headers as before
# async_client: keep the get_db override for auth

@pytest_asyncio.fixture(autouse=True)
async def mock_redis():
    with patch("app.routes.auth.redis") as mock, \
        patch("app.core.dependencies.redis_client") as mock_cache:
        mock.set = AsyncMock(return_value=True)
        mock_cache.get = AsyncMock(return_value=None)
        yield mock

@pytest_asyncio.fixture(autouse=True)
async def mock_celery():
    with patch("app.routes.minutes.summarize_meeting_task") as mock:
        mock.delay = MagicMock(return_value=MagicMock(id="test-task-id"))
        yield mock

@pytest_asyncio.fixture
async def async_client(setup_db):
    app.dependency_overrides[get_db] = override_get_db
    # No `async with` — the __aexit__ teardown hits a closed loop under
    # pytest-asyncio's per-test loop. Create without the context manager.
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    yield client
    await client.aclose()
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def auth_headers(async_client):
    response = await async_client.post("/api/v1/auth/register", json={
        "email": "testuser@example.com",
        "password": "testpass123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
