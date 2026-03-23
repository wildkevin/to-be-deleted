import uuid
from datetime import datetime
from sqlalchemy import String, Text, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base


class MarketplaceItem(Base):
    __tablename__ = "marketplace_items"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String)  # mcp | skill
    config: Mapped[dict] = mapped_column(JSON)
    file_path: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")  # pending | approved | rejected
    submitted_by: Mapped[str] = mapped_column(String)
    reviewed_by: Mapped[str | None] = mapped_column(String, nullable=True)
    status_changed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    discovered_tools: Mapped[list | None] = mapped_column(JSON, nullable=True)  # for mcp: list of tool names
