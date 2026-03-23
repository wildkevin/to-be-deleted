import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_agent_runner_streams_tokens():
    """Agent runner yields SSE events for a simple response."""
    from backend.core.agent_runner import run_agent_stream

    mock_agent_db = MagicMock()
    mock_agent_db.name = "TestAgent"
    mock_agent_db.system_prompt = "You are helpful."
    mock_agent_db.model = "gpt-4.1"
    mock_agent_db.mcp_tools = []
    mock_agent_db.skills = []

    events = []
    with patch("agent_framework.Agent") as MockAgent, \
         patch("agent_framework.AgentContext"), \
         patch("agent_framework.Message"), \
         patch("agent_framework.Role"):
        mock_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "Hello!"
        mock_instance.run = AsyncMock(return_value=mock_response)
        MockAgent.return_value = mock_instance

        async for event in run_agent_stream(mock_agent_db, "Hi", [], []):
            events.append(event)

    event_types = [e["event"] for e in events]
    assert "step_start" in event_types
    assert "step_end" in event_types
    assert "done" in event_types
