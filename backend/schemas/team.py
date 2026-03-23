from pydantic import BaseModel
from datetime import datetime


class TeamAgentEntry(BaseModel):
    agent_id: str
    position: int


class TeamCreate(BaseModel):
    name: str
    description: str
    mode: str  # sequential | orchestrator | loop
    agents: list[TeamAgentEntry]
    orchestrator_agent_id: str | None = None
    loop_max_iterations: int | None = 5
    loop_stop_signal: str | None = None


class AgentSummary(BaseModel):
    id: str
    name: str
    model_config = {"from_attributes": True}


class TeamAgentRead(BaseModel):
    agent: AgentSummary | None = None
    position: int
    model_config = {"from_attributes": True}


class TeamRead(BaseModel):
    id: str
    name: str
    description: str
    mode: str
    orchestrator_agent_id: str | None
    loop_max_iterations: int | None
    loop_stop_signal: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    agents: list[TeamAgentRead] | None = None
    model_config = {"from_attributes": True}


class PaginatedTeams(BaseModel):
    items: list[TeamRead]
    total: int
    page: int
    limit: int
