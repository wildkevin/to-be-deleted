import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, Table, Column, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base

agent_mcp_tools = Table(
    "agent_mcp_tools", Base.metadata,
    Column("agent_id", String, ForeignKey("agents.id"), primary_key=True),
    Column("marketplace_item_id", String, ForeignKey("marketplace_items.id"), primary_key=True),
)

agent_skills = Table(
    "agent_skills", Base.metadata,
    Column("agent_id", String, ForeignKey("agents.id"), primary_key=True),
    Column("marketplace_item_id", String, ForeignKey("marketplace_items.id"), primary_key=True),
)


class Agent(Base):
    __tablename__ = "agents"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    system_prompt: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String)  # gpt-4.1-mini | gpt-4.1 | gpt-5 | gpt-5.1
    created_by: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    mcp_tools: Mapped[list] = relationship("MarketplaceItem", secondary=agent_mcp_tools, lazy="selectin")
    skills: Mapped[list] = relationship("MarketplaceItem", secondary=agent_skills, lazy="selectin")
    team_memberships: Mapped[list] = relationship("TeamAgent", back_populates="agent")
