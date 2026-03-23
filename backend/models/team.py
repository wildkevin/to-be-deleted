import uuid
from datetime import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class TeamAgent(Base):
    __tablename__ = "team_agents"
    team_id: Mapped[str] = mapped_column(String, ForeignKey("teams.id"), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String, ForeignKey("agents.id"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer)
    agent: Mapped["Agent"] = relationship("Agent", back_populates="team_memberships")


class Team(Base):
    __tablename__ = "teams"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(String)  # sequential | orchestrator | loop
    orchestrator_agent_id: Mapped[str | None] = mapped_column(String, nullable=True)
    loop_max_iterations: Mapped[int | None] = mapped_column(Integer, nullable=True, default=5)
    loop_stop_signal: Mapped[str | None] = mapped_column(String, nullable=True)
    created_by: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    agents: Mapped[list[TeamAgent]] = relationship(
        "TeamAgent", cascade="all, delete-orphan", order_by="TeamAgent.position"
    )
