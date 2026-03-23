import pytest


@pytest.mark.asyncio
async def test_missing_user_header_returns_401(client):
    response = await client.get("/api/agents", headers={})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_valid_user_header_passes(client):
    response = await client.get("/api/agents", headers={"X-CCM-User": "alice"})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_unknown_user_header_returns_401(client):
    response = await client.get("/api/agents", headers={"X-CCM-User": "unknown"})
    assert response.status_code == 401
