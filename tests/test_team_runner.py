import pytest
from unittest.mock import MagicMock, patch


def make_agent(name):
    a = MagicMock()
    a.name = name
    a.system_prompt = f"You are {name}."
    a.model = "gpt-4.1"
    a.mcp_tools = []
    a.skills = []
    return a


def make_team_agent(agent, position):
    ta = MagicMock()
    ta.agent = agent
    ta.position = position
    ta.agent_id = agent.name  # use name as surrogate ID for tests
    return ta


@pytest.mark.asyncio
async def test_sequential_emits_steps():
    from backend.core.team_runner import run_team_stream

    team = MagicMock()
    team.mode = "sequential"
    team.agents = [
        make_team_agent(make_agent("A1"), 0),
        make_team_agent(make_agent("A2"), 1),
    ]

    with patch("backend.core.team_runner.run_agent_stream") as mock_stream:

        async def fake_stream(agent, message, history, attachments):
            yield {"event": "step_start", "data": {"step": 1, "agent_name": agent.name}}
            yield {"event": "token", "data": {"text": f"output from {agent.name}"}}
            yield {"event": "step_end", "data": {"step": 1, "agent_name": agent.name}}
            yield {"event": "done", "data": {"message_id": "x"}}

        mock_stream.side_effect = fake_stream

        events = [e async for e in run_team_stream(team, "hello", [], [])]

    step_starts = [e for e in events if e["event"] == "step_start"]
    assert len(step_starts) == 2  # one per agent


@pytest.mark.asyncio
async def test_loop_stops_at_max_iterations():
    from backend.core.team_runner import run_team_stream

    team = MagicMock()
    team.mode = "loop"
    team.loop_max_iterations = 2
    team.loop_stop_signal = None
    team.agents = [make_team_agent(make_agent("A"), 0)]

    with patch("backend.core.team_runner.run_agent_stream") as mock_stream:

        async def fake_stream(agent, message, history, attachments):
            yield {"event": "token", "data": {"text": "result"}}
            yield {"event": "done", "data": {"message_id": "x"}}

        mock_stream.side_effect = fake_stream

        events = [e async for e in run_team_stream(team, "hello", [], [])]

    done_events = [e for e in events if e["event"] == "done"]
    assert len(done_events) == 1


@pytest.mark.asyncio
async def test_loop_stops_on_signal():
    from backend.core.team_runner import run_team_stream

    team = MagicMock()
    team.mode = "loop"
    team.loop_max_iterations = 10
    team.loop_stop_signal = "DONE"
    team.agents = [make_team_agent(make_agent("A"), 0)]

    with patch("backend.core.team_runner.run_agent_stream") as mock_stream:

        async def fake_stream(agent, message, history, attachments):
            yield {"event": "token", "data": {"text": "Task is DONE"}}
            yield {"event": "done", "data": {"message_id": "x"}}

        mock_stream.side_effect = fake_stream

        events = [e async for e in run_team_stream(team, "hello", [], [])]

    done_events = [e for e in events if e["event"] == "done"]
    assert len(done_events) == 1
