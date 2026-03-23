import pytest

HEADERS = {"X-CCM-User": "alice"}


@pytest.mark.asyncio
async def test_list_agents_empty(client):
    r = await client.get("/api/agents", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["items"] == []


@pytest.mark.asyncio
async def test_create_and_get_agent(client):
    payload = {
        "name": "Credit Bot",
        "description": "desc",
        "system_prompt": "You are a credit analyst.",
        "model": "gpt-4.1",
        "mcp_tool_ids": [],
        "skill_ids": [],
    }
    r = await client.post("/api/agents", json=payload, headers=HEADERS)
    assert r.status_code == 201
    agent_id = r.json()["id"]

    r = await client.get(f"/api/agents/{agent_id}", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["name"] == "Credit Bot"


@pytest.mark.asyncio
async def test_delete_agent(client):
    payload = {
        "name": "Temp",
        "description": "d",
        "system_prompt": "s",
        "model": "gpt-4.1",
        "mcp_tool_ids": [],
        "skill_ids": [],
    }
    r = await client.post("/api/agents", json=payload, headers=HEADERS)
    agent_id = r.json()["id"]
    r = await client.delete(f"/api/agents/{agent_id}", headers=HEADERS)
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_update_agent(client):
    payload = {
        "name": "Original",
        "description": "d",
        "system_prompt": "s",
        "model": "gpt-4.1",
        "mcp_tool_ids": [],
        "skill_ids": [],
    }
    r = await client.post("/api/agents", json=payload, headers=HEADERS)
    agent_id = r.json()["id"]
    updated = {**payload, "name": "Updated"}
    r = await client.put(f"/api/agents/{agent_id}", json=updated, headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["name"] == "Updated"
