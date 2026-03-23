from pydantic import BaseModel
from datetime import datetime

VALID_MODELS = ["gpt-4.1-mini", "gpt-4.1", "gpt-5", "gpt-5.1"]


class AgentCreate(BaseModel):
    name: str
    description: str
    system_prompt: str
    model: str
    mcp_tool_ids: list[str] = []
    skill_ids: list[str] = []


class MarketplaceItemRef(BaseModel):
    id: str
    name: str
    type: str
    model_config = {"from_attributes": True}


class AgentRead(BaseModel):
    id: str
    name: str
    description: str
    system_prompt: str
    model: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    mcp_tools: list[MarketplaceItemRef] | None = None
    skills: list[MarketplaceItemRef] | None = None
    model_config = {"from_attributes": True}


class PaginatedAgents(BaseModel):
    items: list[AgentRead]
    total: int
    page: int
    limit: int
