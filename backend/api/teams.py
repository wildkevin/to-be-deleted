from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload, joinedload
from backend.api.deps import get_db, get_current_user
from backend.models.team import Team, TeamAgent
from backend.models.user import User
from backend.schemas.team import TeamCreate, TeamRead, PaginatedTeams

router = APIRouter(prefix="/api/teams", tags=["teams"])


@router.get("", response_model=PaginatedTeams)
async def list_teams(
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    offset = (page - 1) * limit
    total = (await db.execute(select(func.count(Team.id)))).scalar()
    result = await db.execute(
        select(Team)
        .options(selectinload(Team.agents).joinedload(TeamAgent.agent))
        .offset(offset)
        .limit(limit)
    )
    return PaginatedTeams(items=result.scalars().all(), total=total, page=page, limit=limit)


@router.post("", response_model=TeamRead, status_code=201)
async def create_team(
    body: TeamCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    team = Team(
        name=body.name,
        description=body.description,
        mode=body.mode,
        orchestrator_agent_id=body.orchestrator_agent_id,
        loop_max_iterations=body.loop_max_iterations,
        loop_stop_signal=body.loop_stop_signal,
        created_by=user.id,
    )
    db.add(team)
    await db.flush()
    for entry in body.agents:
        db.add(TeamAgent(team_id=team.id, agent_id=entry.agent_id, position=entry.position))
    await db.commit()
    # Reload with relationships
    result = await db.execute(
        select(Team)
        .options(selectinload(Team.agents).joinedload(TeamAgent.agent))
        .where(Team.id == team.id)
    )
    team = result.scalar_one()
    return team


@router.get("/{team_id}", response_model=TeamRead)
async def get_team(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Team)
        .options(selectinload(Team.agents).joinedload(TeamAgent.agent))
        .where(Team.id == team_id)
    )
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404)
    return team


@router.put("/{team_id}", response_model=TeamRead)
async def update_team(
    team_id: str,
    body: TeamCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Team)
        .options(selectinload(Team.agents).joinedload(TeamAgent.agent))
        .where(Team.id == team_id)
    )
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404)
    for field in [
        "name",
        "description",
        "mode",
        "orchestrator_agent_id",
        "loop_max_iterations",
        "loop_stop_signal",
    ]:
        setattr(team, field, getattr(body, field))
    # Replace agents
    for ta in list(team.agents):
        await db.delete(ta)
    await db.flush()
    for entry in body.agents:
        db.add(TeamAgent(team_id=team.id, agent_id=entry.agent_id, position=entry.position))
    await db.commit()
    await db.refresh(team, ["agents"])
    return team


@router.delete("/{team_id}", status_code=204)
async def delete_team(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404)
    await db.delete(team)
    await db.commit()
