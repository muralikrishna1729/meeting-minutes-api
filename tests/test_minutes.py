import pytest
from httpx import AsyncClient

original_text = "This is a meeting about the Q3 budget. We discussed hiring plans and decided to postpone the product launch until next quarter."

@pytest.mark.asyncio
async def test_upload_text_success(async_client: AsyncClient, auth_headers: dict):
    response = await async_client.post("/api/v1/minutes/upload-text", json={"original_text": original_text}, headers=auth_headers)
    assert response.status_code == 202
    data = response.json()
    assert "meeting_id" in data

@pytest.mark.asyncio
async def test_upload_unauthenticated(async_client: AsyncClient):
    response = await async_client.post("/api/v1/minutes/upload-text", json={"original_text": original_text})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_minute_status(async_client: AsyncClient, auth_headers: dict):
    response = await async_client.post(
        "/api/v1/minutes/upload-text",
        json={"original_text": original_text},
        headers=auth_headers
    )
    assert response.status_code == 202
    data = response.json()
    assert "meeting_id" in data
    meeting_id = data["meeting_id"]
    response = await async_client.get(f"/api/v1/minutes/{meeting_id}/status", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "status" in data

@pytest.mark.asyncio
async def test_get_other_user_minute(async_client: AsyncClient, auth_headers: dict):
    user_a_response = await async_client.post("/api/v1/auth/register", json={
        "email": "usera@example.com", "password": "password123"})
    token_a = user_a_response.json()["access_token"]

    user_b_response = await async_client.post("/api/v1/auth/register", json={
        "email": "userb@example.com", "password": "password123"})
    token_b = user_b_response.json()["access_token"]

    response = await async_client.post(
        "/api/v1/minutes/upload-text",
        json={"original_text": original_text},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert response.status_code == 202
    data = response.json()
    assert "meeting_id" in data
    meeting_id = data["meeting_id"]

    response = await async_client.get(
        f"/api/v1/minutes/{meeting_id}",
        headers={"Authorization": f"Bearer {token_b}"}
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_delete_minute(async_client: AsyncClient, auth_headers: dict):
    response = await async_client.post(
        "/api/v1/minutes/upload-text",
        json={"original_text": original_text},
        headers=auth_headers
    )
    assert response.status_code == 202
    data = response.json()
    assert "meeting_id" in data
    meeting_id = data["meeting_id"]
    response = await async_client.delete(f"/api/v1/minutes/{meeting_id}", headers=auth_headers)
    assert response.status_code == 204
    response = await async_client.delete(f"/api/v1/minutes/{meeting_id}", headers=auth_headers)
    assert response.status_code == 404
