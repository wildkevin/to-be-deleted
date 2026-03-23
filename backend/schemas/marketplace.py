from pydantic import BaseModel
from datetime import datetime


class MarketplaceItemRead(BaseModel):
    id: str
    name: str
    description: str
    type: str
    config: dict
    status: str
    submitted_by: str
    reviewed_by: str | None
    discovered_tools: list | None
    created_at: datetime
    model_config = {"from_attributes": True}


class PaginatedMarketplace(BaseModel):
    items: list[MarketplaceItemRead]
    total: int
    page: int
    limit: int
