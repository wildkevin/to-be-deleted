import pytest

HEADERS = {"X-CCM-User": "alice"}
ADMIN_HEADERS = {"X-CCM-User": "admin"}


@pytest.mark.asyncio
async def test_list_approved_empty(client):
    r = await client.get("/api/marketplace", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["items"] == []


@pytest.mark.asyncio
async def test_approve_reject_requires_admin(client):
    r = await client.post("/api/marketplace/fake-id/approve", headers=HEADERS)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_pending_requires_admin(client):
    r = await client.get("/api/marketplace/pending", headers=HEADERS)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_access_pending(client):
    r = await client.get("/api/marketplace/pending", headers=ADMIN_HEADERS)
    assert r.status_code == 200
    assert r.json()["items"] == []
