import pytest
from httpx import AsyncClient

TEST_USER = {"email": "test@example.com", "password": "testpass123"}

@pytest.mark.asyncio
async def test_register_success(async_client: AsyncClient):
    response = await async_client.post("/api/v1/auth/register", json=TEST_USER)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient):
    await async_client.post("/api/v1/auth/register", json=TEST_USER)
    response = await async_client.post("/api/v1/auth/register", json=TEST_USER)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    await async_client.post("/api/v1/auth/register", json=TEST_USER)
    response = await async_client.post("/api/v1/auth/login", json=TEST_USER)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient):
    await async_client.post("/api/v1/auth/register", json=TEST_USER)
    response = await async_client.post("/api/v1/auth/login", json={"email": TEST_USER["email"], "password": "wrongpassword"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_refresh_token(async_client: AsyncClient):
    await async_client.post("/api/v1/auth/register", json=TEST_USER)
    response = await async_client.post("/api/v1/auth/login", json=TEST_USER)
    assert response.status_code == 200
    data = response.json()
    assert "refresh_token" in data
    token = data["refresh_token"]
    response = await async_client.post("/api/v1/auth/refresh", json={"refresh_token": token})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

@pytest.mark.asyncio
async def test_logout(async_client: AsyncClient):
    await async_client.post("/api/v1/auth/register", json=TEST_USER)
    response = await async_client.post("/api/v1/auth/login", json=TEST_USER)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    token = data["access_token"]
    response = await async_client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
