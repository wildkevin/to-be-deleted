from typing import AsyncGenerator, Any
from backend.config import settings
from backend.core.skill_runner import run_skill


def _sse(event: str, data: dict) -> dict:
    return {"event": event, "data": data}


async def run_agent_stream(
    agent_db,
    message: str,
    history: list[dict],
    attachments: list,
) -> AsyncGenerator[dict, None]:
    from agent_framework import Agent, AgentContext
    from agent_framework import MCPStreamableHTTPTool, FunctionTool
    from agent_framework import Role

    yield _sse("step_start", {"step": 1, "agent_name": agent_db.name})

    try:
        tools = []

        # MCP tools
        for mcp in agent_db.mcp_tools:
            tools.append(
                MCPStreamableHTTPTool(
                    name=mcp.name,
                    url=mcp.config["server_url"],
                    headers=mcp.config.get("auth_headers", {}),
                )
            )

        # Skills as AI functions
        for skill in agent_db.skills:
            async def _invoke(skill_item=skill, **kwargs):
                return await run_skill(
                    skill_item.file_path,
                    skill_item.config["function_name"],
                    kwargs,
                )

            fn = FunctionTool(
                name=skill.name,
                description=skill.description,
                fn=_invoke,
                parameters=skill.config.get("input_schema", {}),
            )
            tools.append(fn)

        # Build context
        file_context = ""
        for att in attachments:
            file_context += f"\n--- File: {att.filename} ---\n{att.extracted_text}\n---\n"

        full_message = f"{file_context}\n{message}".strip() if file_context else message

        # Convert to Message format
        from agent_framework import Message
        messages = [Message(role=Role.USER, content=full_message)]

        agent = Agent(
            name=agent_db.name,
            instructions=agent_db.system_prompt,
            tools=tools if tools else None,
        )

        context = AgentContext(
            agent=agent,
            messages=messages,
            client_kwargs={
                "endpoint": settings.azure_openai_endpoint,
                "api_key": settings.azure_openai_api_key,
                "api_version": settings.azure_openai_api_version,
                "deployment_name": agent_db.model,
            },
        )

        # Stream response
        response = await agent.run(full_message, context=context)
        # Emit content as tokens
        if hasattr(response, "content"):
            for chunk in _chunk_text(response.content):
                yield _sse("token", {"text": chunk})
        yield _sse("step_end", {"step": 1, "agent_name": agent_db.name})

    except Exception as e:
        yield _sse("error", {"code": "azure_error", "message": str(e)})
        return

    yield _sse("done", {"message_id": ""})


def _chunk_text(text: str, size: int = 20) -> list[str]:
    """Split text into chunks to simulate streaming."""
    return [text[i : i + size] for i in range(0, len(text), size)]
