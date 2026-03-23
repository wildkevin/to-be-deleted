import pytest

HEADERS = {"X-CCM-User": "alice"}


@pytest.mark.asyncio
async def test_create_and_get_team(client):
    # Create two agents first
    def mk_agent(name):
        return {
            "name": name,
            "description": "d",
            "system_prompt": "s",
            "model": "gpt-4.1",
            "mcp_tool_ids": [],
            "skill_ids": [],
        }

    a1 = (await client.post("/api/agents", json=mk_agent("A1"), headers=HEADERS)).json()["id"]
    a2 = (await client.post("/api/agents", json=mk_agent("A2"), headers=HEADERS)).json()["id"]

    payload = {
        "name": "Credit Team",
        "description": "d",
        "mode": "sequential",
        "agents": [{"agent_id": a1, "position": 0}, {"agent_id": a2, "position": 1}],
    }
    r = await client.post("/api/teams", json=payload, headers=HEADERS)
    assert r.status_code == 201
    team_id = r.json()["id"]

    r = await client.get(f"/api/teams/{team_id}", headers=HEADERS)
    assert r.json()["name"] == "Credit Team"
    assert len(r.json()["agents"]) == 2


@pytest.mark.asyncio
async def test_delete_agent_in_team_returns_409(client):
    payload = {
        "name": "Solo",
        "description": "d",
        "system_prompt": "s",
        "model": "gpt-4.1",
        "mcp_tool_ids": [],
        "skill_ids": [],
    }
    agent_id = (await client.post("/api/agents", json=payload, headers=HEADERS)).json()["id"]
    team_payload = {
        "name": "T",
        "description": "d",
        "mode": "sequential",
        "agents": [{"agent_id": agent_id, "position": 0}],
    }
    await client.post("/api/teams", json=team_payload, headers=HEADERS)
    r = await client.delete(f"/api/agents/{agent_id}", headers=HEADERS)
    assert r.status_code == 409
