import uuid
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.api.deps import get_db, get_current_user, get_admin_user
from backend.models.marketplace import MarketplaceItem
from backend.models.user import User
from backend.schemas.marketplace import MarketplaceItemRead, PaginatedMarketplace
from backend.storage.local import storage

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])


@router.get("", response_model=PaginatedMarketplace)
async def list_approved(
    type: str | None = None,
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(MarketplaceItem).where(MarketplaceItem.status == "approved")
    if type:
        q = q.where(MarketplaceItem.type == type)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    result = await db.execute(q.offset((page - 1) * limit).limit(limit))
    return PaginatedMarketplace(items=result.scalars().all(), total=total, page=page, limit=limit)


@router.post("/submit", response_model=MarketplaceItemRead, status_code=201)
async def submit_item(
    name: str = Form(...),
    description: str = Form(...),
    type: str = Form(...),
    server_url: str | None = Form(None),
    auth_headers: str | None = Form(None),
    function_name: str | None = Form(None),
    input_schema: str | None = Form(None),
    output_schema: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if type == "mcp":
        config = {
            "server_url": server_url,
            "auth_headers": json.loads(auth_headers or "{}"),
        }
        # Attempt tool discovery
        discovered = await _discover_mcp_tools(server_url, json.loads(auth_headers or "{}"))
        item = MarketplaceItem(
            name=name,
            description=description,
            type="mcp",
            config=config,
            submitted_by=user.id,
            discovered_tools=discovered,
        )
    elif type == "skill":
        if not file:
            raise HTTPException(status_code=400, detail="Skill requires a .py file")
        file_content = await file.read()
        path = f"skills/{uuid.uuid4()}_{file.filename}"
        stored_path = await storage.save(path, file_content)
        config = {
            "function_name": function_name,
            "input_schema": json.loads(input_schema or "{}"),
            "output_schema": json.loads(output_schema or "{}"),
        }
        item = MarketplaceItem(
            name=name,
            description=description,
            type="skill",
            config=config,
            file_path=stored_path,
            submitted_by=user.id,
        )
    else:
        raise HTTPException(status_code=400, detail="type must be mcp or skill")
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def _discover_mcp_tools(server_url: str, headers: dict) -> list[str]:
    try:
        from agent_framework import MCPStreamableHTTPTool

        tool = MCPStreamableHTTPTool(
            name="discovery", url=server_url, headers=headers, load_prompts=False
        )
        async with tool:
            return [f.name for f in tool.functions] if tool.functions else []
    except Exception:
        # Spec: if the backend can't reach/discover the MCP server, reject submission with 400.
        raise HTTPException(status_code=400, detail="Could not connect to MCP server")


@router.get("/pending", response_model=PaginatedMarketplace)
async def list_pending(
    page: int = 1,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    q = select(MarketplaceItem).where(MarketplaceItem.status == "pending")
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    result = await db.execute(q.offset((page - 1) * limit).limit(limit))
    return PaginatedMarketplace(items=result.scalars().all(), total=total, page=page, limit=limit)


@router.post("/{item_id}/approve", response_model=MarketplaceItemRead)
async def approve_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    return await _set_status(item_id, "approved", admin.id, db)


@router.post("/{item_id}/reject", response_model=MarketplaceItemRead)
async def reject_item(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    return await _set_status(item_id, "rejected", admin.id, db)


async def _set_status(item_id, status, reviewer_id, db):
    result = await db.execute(select(MarketplaceItem).where(MarketplaceItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404)
    item.status = status
    item.reviewed_by = reviewer_id
    item.status_changed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(item)
    return item
