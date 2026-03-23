import pytest

HEADERS = {"X-CCM-User": "alice"}


@pytest.mark.asyncio
async def test_create_and_list_conversations(client):
    # Need an agent first
    agent_payload = {
        "name": "Bot",
        "description": "d",
        "system_prompt": "s",
        "model": "gpt-4.1",
        "mcp_tool_ids": [],
        "skill_ids": [],
    }
    agent_id = (await client.post("/api/agents", json=agent_payload, headers=HEADERS)).json()["id"]

    r = await client.post(
        "/api/conversations",
        json={"title": "Q1 Analysis", "target_type": "agent", "target_id": agent_id},
        headers=HEADERS,
    )
    assert r.status_code == 201
    conv_id = r.json()["id"]

    r = await client.get("/api/conversations", headers=HEADERS)
    assert any(c["id"] == conv_id for c in r.json()["items"])


@pytest.mark.asyncio
async def test_delete_conversation(client):
    agent_id = (
        await client.post(
            "/api/agents",
            json={
                "name": "B",
                "description": "d",
                "system_prompt": "s",
                "model": "gpt-4.1",
                "mcp_tool_ids": [],
                "skill_ids": [],
            },
            headers=HEADERS,
        )
    ).json()["id"]
    conv_id = (
        await client.post(
            "/api/conversations",
            json={"title": "t", "target_type": "agent", "target_id": agent_id},
            headers=HEADERS,
        )
    ).json()["id"]
    r = await client.delete(f"/api/conversations/{conv_id}", headers=HEADERS)
    assert r.status_code == 204
