import json
import uuid
import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from backend.api.deps import get_db, get_current_user
from backend.models.conversation import Conversation, Message, Attachment
from backend.models.user import User

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

ALLOWED_MIME = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}
MAX_SIZE = 20 * 1024 * 1024  # 20MB


class ConversationCreate(BaseModel):
    title: str
    target_type: str
    target_id: str


class ConversationRead(BaseModel):
    id: str
    title: str
    target_type: str
    target_id: str
    created_by: str
    model_config = {"from_attributes": True}


class PaginatedConversations(BaseModel):
    items: list[ConversationRead]
    total: int
    page: int
    limit: int


class ChatRequest(BaseModel):
    message: str
    attachment_ids: list[str] = []


@router.get("", response_model=PaginatedConversations)
async def list_conversations(
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(Conversation).where(Conversation.created_by == user.id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    result = await db.execute(q.offset((page - 1) * limit).limit(limit))
    return PaginatedConversations(items=result.scalars().all(), total=total, page=page, limit=limit)


@router.post("", response_model=ConversationRead, status_code=201)
async def create_conversation(
    body: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from sqlalchemy.orm import selectinload

    conv = Conversation(
        title=body.title,
        target_type=body.target_type,
        target_id=body.target_id,
        created_by=user.id,
    )
    db.add(conv)
    await db.commit()
    # Reload with relationships
    result = await db.execute(
        select(Conversation)
        .options(
            selectinload(Conversation.messages),
            selectinload(Conversation.attachments)
        )
        .where(Conversation.id == conv.id)
    )
    conv = result.scalar_one()
    return conv


@router.get("/{conv_id}")
async def get_conversation(
    conv_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Conversation)
        .options(
            selectinload(Conversation.messages),
            selectinload(Conversation.attachments)
        )
        .where(Conversation.id == conv_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404)
    return conv


@router.delete("/{conv_id}", status_code=204)
async def delete_conversation(
    conv_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.attachments))
        .where(Conversation.id == conv_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404)
    # Delete stored files
    for att in conv.attachments or []:
        if os.path.exists(att.file_path):
            os.remove(att.file_path)
    await db.delete(conv)
    await db.commit()


@router.post("/{conv_id}/upload")
async def upload_file(
    conv_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from backend.core.file_extractor import extract_text
    from backend.storage.local import storage

    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404)

    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 20MB limit")

    try:
        text = extract_text(file.filename, data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not extract text: {e}")

    path = f"{conv_id}/{uuid.uuid4()}_{file.filename}"
    stored = await storage.save(path, data)

    att = Attachment(
        conversation_id=conv_id,
        filename=file.filename,
        file_path=stored,
        mime_type=file.content_type or "",
        size=len(data),
        extracted_text=text,
    )
    db.add(att)
    await db.commit()
    await db.refresh(att)
    return {
        "attachment_id": att.id,
        "filename": att.filename,
        "mime_type": att.mime_type,
        "size": att.size,
        "extracted_text_preview": text[:500],
    }


@router.post("/{conv_id}/chat")
async def chat(
    conv_id: str,
    body: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404)

    # Fetch history (last 20 messages)
    history = [{"role": m.role, "content": m.content} for m in conv.messages[-20:]]

    # Fetch attachments
    attachments = []
    if body.attachment_ids:
        att_result = await db.execute(
            select(Attachment).where(Attachment.id.in_(body.attachment_ids))
        )
        attachments = att_result.scalars().all()

    agent_db = None
    if conv.target_type == "agent":
        from backend.models.agent import Agent
        from backend.core.agent_runner import run_agent_stream

        agent_result = await db.execute(select(Agent).where(Agent.id == conv.target_id))
        agent_db = agent_result.scalar_one_or_none()
        if not agent_db:
            raise HTTPException(status_code=404, detail="Agent not found")
        stream = run_agent_stream(agent_db, body.message, history, attachments)
    else:
        from backend.models.team import Team
        from backend.core.team_runner import run_team_stream

        team_result = await db.execute(select(Team).where(Team.id == conv.target_id))
        team_db = team_result.scalar_one_or_none()
        if not team_db:
            raise HTTPException(status_code=404, detail="Team not found")
        stream = run_team_stream(team_db, body.message, history, attachments)

    # Save user message
    user_msg = Message(
        conversation_id=conv_id, role="user", content={"text": body.message}
    )
    db.add(user_msg)
    await db.commit()

    # Link attachments to message
    for att in attachments:
        att.message_id = user_msg.id
    if attachments:
        await db.commit()

    async def event_generator():
        full_response = []
        async for event in stream:
            data = json.dumps(event["data"])
            yield f"event: {event['event']}\ndata: {data}\n\n"
            if event["event"] == "token":
                full_response.append(event["data"]["text"])
            if event["event"] in ("done", "error"):
                break
        # Persist assistant message
        if full_response:
            agent_name = getattr(agent_db, "name", "") if agent_db else ""
            asst_msg = Message(
                conversation_id=conv_id,
                role="assistant",
                content={"text": "".join(full_response), "agent_name": agent_name},
            )
            db.add(asst_msg)
            await db.commit()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
