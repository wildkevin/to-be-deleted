import uuid
from datetime import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import Base


class Attachment(Base):
    __tablename__ = "attachments"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id: Mapped[str | None] = mapped_column(String, ForeignKey("messages.id"), nullable=True)
    conversation_id: Mapped[str] = mapped_column(String, ForeignKey("conversations.id"))
    filename: Mapped[str] = mapped_column(String)
    file_path: Mapped[str] = mapped_column(String)
    mime_type: Mapped[str] = mapped_column(String)
    size: Mapped[int] = mapped_column(Integer)
    extracted_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String, ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String)  # user | assistant | tool
    content: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    attachments: Mapped[list[Attachment]] = relationship("Attachment", foreign_keys=[Attachment.message_id])


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String)
    target_type: Mapped[str] = mapped_column(String)  # agent | team
    target_id: Mapped[str] = mapped_column(String)
    created_by: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    messages: Mapped[list[Message]] = relationship(
        "Message", cascade="all, delete-orphan", order_by="Message.created_at"
    )
    attachments: Mapped[list[Attachment]] = relationship(
        "Attachment",
        foreign_keys=[Attachment.conversation_id],
        cascade="all, delete-orphan",
        primaryjoin="Conversation.id == Attachment.conversation_id",
    )
