from typing import AsyncGenerator
from backend.core.agent_runner import run_agent_stream, _sse


async def run_team_stream(
    team_db, message: str, history: list, attachments: list
) -> AsyncGenerator[dict, None]:
    if team_db.mode == "sequential":
        async for event in _sequential(team_db, message, history, attachments):
            yield event
    elif team_db.mode == "orchestrator":
        async for event in _orchestrator(team_db, message, history, attachments):
            yield event
    elif team_db.mode == "loop":
        async for event in _loop(team_db, message, history, attachments):
            yield event


async def _sequential(team_db, message, history, attachments):
    current_input = message
    agents = sorted(team_db.agents, key=lambda ta: ta.position)
    for i, team_agent in enumerate(agents):
        agent = team_agent.agent
        is_last = i == len(agents) - 1
        output_tokens = []

        async for event in run_agent_stream(
            agent, current_input, history, attachments if i == 0 else []
        ):
            if is_last:
                yield event  # stream final agent's tokens to user
            else:
                # Intermediate: only emit step markers, buffer output
                if event["event"] in ("step_start", "step_end"):
                    yield event
                elif event["event"] == "token":
                    output_tokens.append(event["data"]["text"])
                elif event["event"] == "error":
                    yield event
                    return

        if not is_last:
            current_input = "".join(output_tokens)


async def _orchestrator(team_db, message, history, attachments):
    # Find lead agent
    lead_ta = next(
        (ta for ta in team_db.agents if ta.agent_id == team_db.orchestrator_agent_id),
        team_db.agents[0],
    )
    specialists = [ta.agent for ta in team_db.agents if ta.agent_id != lead_ta.agent_id]

    # Lead agent gets specialist descriptions injected into its system prompt
    specialist_info = "\n".join(f"- {s.name}: {s.description}" for s in specialists)
    lead_agent = lead_ta.agent
    augmented_prompt = (
        f"{lead_agent.system_prompt}\n\n"
        f"You can delegate to these specialists:\n{specialist_info}\n"
        f"When you need a specialist, say 'DELEGATE TO <name>: <task>'."
    )

    patched_agent = _patch_prompt(lead_agent, augmented_prompt)
    yield _sse("step_start", {"step": 1, "agent_name": lead_agent.name})
    async for event in run_agent_stream(patched_agent, message, history, attachments):
        if event["event"] in ("token", "step_end", "done", "error"):
            yield event


def _patch_prompt(agent, new_prompt):
    """Return a copy of agent with a different system prompt (no DB write)."""
    from types import SimpleNamespace

    return SimpleNamespace(
        name=agent.name,
        system_prompt=new_prompt,
        model=agent.model,
        mcp_tools=agent.mcp_tools,
        skills=agent.skills,
    )


async def _loop(team_db, message, history, attachments):
    max_iter = team_db.loop_max_iterations or 5
    stop_signal = team_db.loop_stop_signal
    agents = sorted(team_db.agents, key=lambda ta: ta.position)
    current_input = message

    for iteration in range(max_iter):
        step_offset = iteration * len(agents)
        last_output = []

        for i, team_agent in enumerate(agents):
            is_last_agent = i == len(agents) - 1
            is_last_iter = iteration == max_iter - 1
            stream_tokens = is_last_agent and is_last_iter
            agent = team_agent.agent
            step = step_offset + i + 1

            yield _sse("step_start", {"step": step, "agent_name": agent.name})
            agent_output = []
            async for event in run_agent_stream(
                agent,
                current_input,
                history,
                attachments if iteration == 0 and i == 0 else [],
            ):
                if event["event"] == "token":
                    agent_output.append(event["data"]["text"])
                    if stream_tokens:
                        yield event
                elif event["event"] in ("step_end", "error"):
                    yield event
            yield _sse("step_end", {"step": step, "agent_name": agent.name})

            if is_last_agent:
                last_output = agent_output
                current_input = "".join(agent_output)

        # Check stop signal after full iteration
        full_output = "".join(last_output)
        if stop_signal and stop_signal.lower() in full_output.lower():
            break

    yield _sse("done", {"message_id": ""})
