from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.api.deps import get_db, get_current_user
from backend.models.agent import Agent
from backend.models.marketplace import MarketplaceItem
from backend.models.team import TeamAgent
from backend.schemas.agent import AgentCreate, AgentRead, PaginatedAgents
from backend.models.user import User

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("", response_model=PaginatedAgents)
async def list_agents(
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    offset = (page - 1) * limit
    total = (await db.execute(select(func.count(Agent.id)))).scalar()
    result = await db.execute(select(Agent).offset(offset).limit(limit))
    return PaginatedAgents(items=result.scalars().all(), total=total, page=page, limit=limit)


@router.post("", response_model=AgentRead, status_code=201)
async def create_agent(
    body: AgentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    agent = Agent(
        name=body.name,
        description=body.description,
        system_prompt=body.system_prompt,
        model=body.model,
        created_by=user.id,
    )
    if body.mcp_tool_ids:
        r = await db.execute(
            select(MarketplaceItem).where(
                MarketplaceItem.id.in_(body.mcp_tool_ids),
                MarketplaceItem.type == "mcp",
                MarketplaceItem.status == "approved",
            )
        )
        agent.mcp_tools = r.scalars().all()
    if body.skill_ids:
        r = await db.execute(
            select(MarketplaceItem).where(
                MarketplaceItem.id.in_(body.skill_ids),
                MarketplaceItem.type == "skill",
                MarketplaceItem.status == "approved",
            )
        )
        agent.skills = r.scalars().all()
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404)
    return agent


@router.put("/{agent_id}", response_model=AgentRead)
async def update_agent(
    agent_id: str,
    body: AgentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404)
    agent.name = body.name
    agent.description = body.description
    agent.system_prompt = body.system_prompt
    agent.model = body.model
    await db.commit()
    await db.refresh(agent)
    return agent


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Block deletion if agent is in any team
    membership = await db.execute(select(TeamAgent).where(TeamAgent.agent_id == agent_id))
    if membership.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Agent is a member of a team. Remove it first.")
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404)
    await db.delete(agent)
    await db.commit()
