# CCM Agent Hub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the CCM Agent Hub — an internal web app for Credit Capital Management analysts to create, share, and interact with AI agents and agent teams powered by Azure OpenAI.

**Architecture:** FastAPI backend (SQLite, SSE streaming, agent-framework==1.0.0rc4) + React SPA (Vite + TypeScript). Agent execution uses `agent_framework.ChatAgent` with `MCPStreamableHTTPTool` for MCP servers and sandboxed subprocesses for skills. Team modes (sequential, orchestrator, loop) implemented in `team_runner.py`.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy (async), aiosqlite, agent-framework==1.0.0rc4, React 18, Vite, TypeScript, TailwindCSS, React Query

**Spec:** `docs/superpowers/specs/2026-03-23-ccm-agent-hub-design.md`

---

## File Map

```
backend/
├── main.py                     # FastAPI app, router registration, CORS
├── config.py                   # Pydantic Settings from env vars
├── database.py                 # Async SQLAlchemy engine + session
├── models/
│   ├── user.py                 # User
│   ├── agent.py                # Agent, AgentMCPTool (join), AgentSkill (join)
│   ├── team.py                 # Team, TeamAgent (join)
│   ├── marketplace.py          # MarketplaceItem
│   └── conversation.py         # Conversation, Message, Attachment
├── schemas/
│   ├── agent.py                # AgentCreate, AgentRead, AgentUpdate
│   ├── team.py                 # TeamCreate, TeamRead
│   ├── marketplace.py          # MarketplaceItemRead, MCPSubmit, SkillSubmit
│   └── conversation.py         # ConversationRead, MessageRead, ChatRequest
├── api/
│   ├── deps.py                 # get_db, get_current_user dependencies
│   ├── agents.py               # CRUD routes for agents
│   ├── teams.py                # CRUD routes for teams
│   ├── marketplace.py          # Submit, approve, reject, list routes
│   └── conversations.py        # Conversation CRUD + chat SSE + file upload
├── core/
│   ├── agent_runner.py         # Single agent execution via ChatAgent
│   ├── team_runner.py          # Sequential / orchestrator / loop modes
│   └── skill_runner.py         # Skill subprocess execution
└── storage/
    ├── base.py                 # StorageClient ABC
    └── local.py                # LocalStorageClient

tests/
├── conftest.py                 # DB fixtures, test client, seed data
├── test_agents.py
├── test_teams.py
├── test_marketplace.py
├── test_conversations.py
├── test_agent_runner.py
└── test_skill_runner.py

frontend/
├── vite.config.ts              # Proxy /api → backend
├── src/
│   ├── App.tsx                 # Router setup
│   ├── api/
│   │   ├── client.ts           # Axios instance with X-CCM-User header
│   │   ├── agents.ts
│   │   ├── teams.ts
│   │   ├── marketplace.ts
│   │   └── conversations.ts
│   ├── pages/
│   │   ├── Hub/index.tsx       # Browse grid: agents, teams, MCPs, skills
│   │   ├── Builder/
│   │   │   ├── AgentBuilder.tsx
│   │   │   └── TeamBuilder.tsx
│   │   └── Playground/index.tsx
│   └── components/
│       ├── ItemCard.tsx        # Reusable hub card
│       ├── ChatWindow.tsx      # SSE-driven chat
│       ├── StepTrace.tsx       # Collapsible agent steps
│       └── FileUpload.tsx
```

---

## Phase 1: Project Foundation

### Task 1: Backend project setup

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/config.py`
- Create: `backend/database.py`
- Create: `backend/main.py`
- Create: `.env.example`

- [ ] **Step 1: Create backend directory and requirements**

```
backend/requirements.txt
```
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy[asyncio]==2.0.36
aiosqlite==0.20.0
pydantic-settings==2.4.0
python-multipart==0.0.12
pdfplumber==0.11.4
openpyxl==3.1.5
python-docx==1.1.2
agent-framework==1.0.0rc4
pytest==8.3.3
pytest-asyncio==0.24.0
httpx==0.27.2
```

- [ ] **Step 2: Create `.env.example`**

```
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_API_VERSION=2025-03-01-preview
DATABASE_URL=sqlite+aiosqlite:///./ccm_hub.db
STORAGE_PATH=./uploads
CORS_ORIGINS=http://localhost:5173
CONTEXT_WINDOW_MESSAGES=20
```

- [ ] **Step 3: Create `backend/config.py`**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    azure_openai_endpoint: str
    azure_openai_api_key: str
    azure_openai_api_version: str = "2025-03-01-preview"
    database_url: str = "sqlite+aiosqlite:///./ccm_hub.db"
    storage_path: str = "./uploads"
    cors_origins: list[str] = ["http://localhost:5173"]
    context_window_messages: int = 20

    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 4: Create `backend/database.py`**

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from backend.config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

- [ ] **Step 5: Create `backend/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import engine, Base

app = FastAPI(title="CCM Agent Hub")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Install dependencies and verify startup**

```bash
cd backend && pip install -r requirements.txt --pre
cp ../.env.example ../.env
cd .. && uvicorn backend.main:app --reload
```
Expected: server starts, `GET /health` returns `{"status": "ok"}`

- [ ] **Step 7: Commit**

```bash
git add backend/ .env.example
git commit -m "feat: backend project setup with FastAPI, config, and DB engine"
```

---

### Task 2: Frontend project setup

**Files:**
- Create: `frontend/` (Vite scaffold)
- Create: `frontend/vite.config.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Scaffold Vite React TypeScript project**

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend && npm install
npm install react-router-dom @tanstack/react-query axios
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

- [ ] **Step 2: Configure Vite proxy in `frontend/vite.config.ts`**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
```

- [ ] **Step 3: Create `frontend/src/api/client.ts`**

```typescript
import axios from 'axios'

const client = axios.create({ baseURL: '/api' })

client.interceptors.request.use((config) => {
  const user = localStorage.getItem('ccm_user') || 'dev-user'
  config.headers['X-CCM-User'] = user
  return config
})

export default client
```

- [ ] **Step 4: Create minimal `frontend/src/App.tsx` with routing**

```typescript
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<div>Hub coming soon</div>} />
          <Route path="/builder/agent" element={<div>Agent Builder coming soon</div>} />
          <Route path="/builder/team" element={<div>Team Builder coming soon</div>} />
          <Route path="/playground/:type/:id" element={<div>Playground coming soon</div>} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
```

- [ ] **Step 5: Verify frontend starts**

```bash
cd frontend && npm run dev
```
Expected: Vite dev server on port 5173, placeholder routes render.

- [ ] **Step 6: Commit**

```bash
git add frontend/
git commit -m "feat: frontend scaffold with Vite, React Router, React Query, Tailwind"
```

---

## Phase 2: Database Models

### Task 3: User and auth middleware

**Files:**
- Create: `backend/models/user.py`
- Create: `backend/api/deps.py`
- Test: `tests/conftest.py`

- [ ] **Step 1: Write failing test**

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.main import app
from backend.database import Base, get_db

TEST_DB = "sqlite+aiosqlite:///./test.db"

@pytest_asyncio.fixture
async def db():
    engine = create_async_engine(TEST_DB)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        # Seed known users for header-based auth.
        # Spec: missing or unknown `X-CCM-User` must return 401 (no auto-create).
        from backend.models.user import User
        session.add_all([
            User(username="alice", display_name="Alice", is_admin=False),
            User(username="admin", display_name="Admin", is_admin=True),
        ])
        await session.commit()
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def client(db):
    async def override_db():
        yield db
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

```python
# tests/test_auth.py
import pytest

@pytest.mark.asyncio
async def test_missing_user_header_returns_401(client):
    response = await client.get("/api/agents", headers={})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_valid_user_header_passes(client):
    response = await client.get("/api/agents", headers={"X-CCM-User": "alice"})
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_unknown_user_header_returns_401(client):
    response = await client.get("/api/agents", headers={"X-CCM-User": "unknown"})
    assert response.status_code == 401
```

- [ ] **Step 2: Run tests — expect failure**

```bash
cd backend && pytest ../tests/test_auth.py -v
```
Expected: FAIL — routes don't exist yet.

- [ ] **Step 3: Create `backend/models/user.py`**

```python
import uuid
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from backend.database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
```

- [ ] **Step 4: Create `backend/api/deps.py`**

```python
from fastapi import Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.models.user import User

async def get_current_user(
    x_ccm_user: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not x_ccm_user:
        raise HTTPException(status_code=401, detail="X-CCM-User header required")
    result = await db.execute(select(User).where(User.username == x_ccm_user))
    user = result.scalar_one_or_none()
    if not user:
        # Spec: unknown users must 401 (no auto-create).
        raise HTTPException(status_code=401, detail="Unknown user")
    return user

async def get_admin_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
```

- [ ] **Step 5: Register a stub agents router in `main.py` so `/api/agents` exists**

```python
# backend/api/agents.py (stub)
from fastapi import APIRouter, Depends
from backend.api.deps import get_current_user

router = APIRouter(prefix="/api/agents", tags=["agents"])

@router.get("")
async def list_agents(user=Depends(get_current_user)):
    return {"items": [], "total": 0, "page": 1, "limit": 20}
```

Add to `main.py`:
```python
from backend.api import agents
app.include_router(agents.router)
```

- [ ] **Step 6: Run tests — expect pass**

```bash
pytest ../tests/test_auth.py -v
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/ tests/
git commit -m "feat: user model, auth middleware, X-CCM-User header validation"
```

---

### Task 4: Core data models

**Files:**
- Create: `backend/models/agent.py`
- Create: `backend/models/team.py`
- Create: `backend/models/marketplace.py`
- Create: `backend/models/conversation.py`

- [ ] **Step 1: Create `backend/models/agent.py`**

```python
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
```

- [ ] **Step 2: Create `backend/models/marketplace.py`**

```python
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
```

- [ ] **Step 3: Create `backend/models/team.py`**

```python
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
    agents: Mapped[list[TeamAgent]] = relationship("TeamAgent", cascade="all, delete-orphan",
                                                    order_by="TeamAgent.position")
```

- [ ] **Step 4: Create `backend/models/conversation.py`**

```python
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
    messages: Mapped[list[Message]] = relationship("Message", cascade="all, delete-orphan",
                                                    order_by="Message.created_at")
    attachments: Mapped[list[Attachment]] = relationship("Attachment",
                                                          foreign_keys=[Attachment.conversation_id],
                                                          cascade="all, delete-orphan")
```

- [ ] **Step 5: Import all models in `main.py` so tables are created**

```python
# Add to backend/main.py imports (before startup event)
from backend.models import user, agent, team, marketplace, conversation  # noqa
```

- [ ] **Step 6: Write model smoke test**

```python
# tests/test_models.py
import pytest
from sqlalchemy import select
from backend.models.user import User
from backend.models.agent import Agent
from backend.models.marketplace import MarketplaceItem

@pytest.mark.asyncio
async def test_create_user(db):
    user = User(username="alice", display_name="Alice")
    db.add(user)
    await db.commit()
    result = await db.execute(select(User).where(User.username == "alice"))
    assert result.scalar_one().display_name == "Alice"

@pytest.mark.asyncio
async def test_create_agent(db):
    user = User(username="bob", display_name="Bob")
    db.add(user)
    await db.commit()
    agent = Agent(name="Credit Bot", description="desc", system_prompt="You are...",
                  model="gpt-4.1", created_by=user.id)
    db.add(agent)
    await db.commit()
    result = await db.execute(select(Agent).where(Agent.name == "Credit Bot"))
    assert result.scalar_one() is not None
```

- [ ] **Step 7: Run tests**

```bash
pytest ../tests/test_models.py -v
```
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add backend/models/ tests/test_models.py
git commit -m "feat: all SQLAlchemy models — User, Agent, Team, MarketplaceItem, Conversation"
```

---

## Phase 3: Backend APIs

### Task 5: Agents CRUD API

**Files:**
- Create: `backend/schemas/agent.py`
- Modify: `backend/api/agents.py`
- Test: `tests/test_agents.py`

- [ ] **Step 1: Create `backend/schemas/agent.py`**

```python
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
    mcp_tools: list[MarketplaceItemRef] = []
    skills: list[MarketplaceItemRef] = []
    model_config = {"from_attributes": True}

class PaginatedAgents(BaseModel):
    items: list[AgentRead]
    total: int
    page: int
    limit: int
```

- [ ] **Step 2: Write failing tests**

```python
# tests/test_agents.py
import pytest

HEADERS = {"X-CCM-User": "alice"}

@pytest.mark.asyncio
async def test_list_agents_empty(client):
    r = await client.get("/api/agents", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["items"] == []

@pytest.mark.asyncio
async def test_create_and_get_agent(client):
    payload = {"name": "Credit Bot", "description": "desc",
               "system_prompt": "You are a credit analyst.", "model": "gpt-4.1",
               "mcp_tool_ids": [], "skill_ids": []}
    r = await client.post("/api/agents", json=payload, headers=HEADERS)
    assert r.status_code == 201
    agent_id = r.json()["id"]

    r = await client.get(f"/api/agents/{agent_id}", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["name"] == "Credit Bot"

@pytest.mark.asyncio
async def test_delete_agent(client):
    payload = {"name": "Temp", "description": "d", "system_prompt": "s",
               "model": "gpt-4.1", "mcp_tool_ids": [], "skill_ids": []}
    r = await client.post("/api/agents", json=payload, headers=HEADERS)
    agent_id = r.json()["id"]
    r = await client.delete(f"/api/agents/{agent_id}", headers=HEADERS)
    assert r.status_code == 204
```

- [ ] **Step 3: Run — expect failure**

```bash
pytest ../tests/test_agents.py -v
```

- [ ] **Step 4: Implement `backend/api/agents.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.api.deps import get_db, get_current_user
from backend.models.agent import Agent
from backend.models.marketplace import MarketplaceItem
from backend.models.team import TeamAgent
from backend.schemas.agent import AgentCreate, AgentRead, PaginatedAgents
from backend.models.user import User

router = APIRouter(prefix="/api/agents", tags=["agents"])

@router.get("", response_model=PaginatedAgents)
async def list_agents(page: int = 1, limit: int = 20,
                      db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)):
    offset = (page - 1) * limit
    total = (await db.execute(select(func.count(Agent.id)))).scalar()
    result = await db.execute(select(Agent).offset(offset).limit(limit))
    return PaginatedAgents(items=result.scalars().all(), total=total, page=page, limit=limit)

@router.post("", response_model=AgentRead, status_code=201)
async def create_agent(body: AgentCreate, db: AsyncSession = Depends(get_db),
                       user: User = Depends(get_current_user)):
    agent = Agent(name=body.name, description=body.description,
                  system_prompt=body.system_prompt, model=body.model,
                  created_by=user.id)
    if body.mcp_tool_ids:
        r = await db.execute(select(MarketplaceItem).where(
            MarketplaceItem.id.in_(body.mcp_tool_ids),
            MarketplaceItem.type == "mcp", MarketplaceItem.status == "approved"))
        agent.mcp_tools = r.scalars().all()
    if body.skill_ids:
        r = await db.execute(select(MarketplaceItem).where(
            MarketplaceItem.id.in_(body.skill_ids),
            MarketplaceItem.type == "skill", MarketplaceItem.status == "approved"))
        agent.skills = r.scalars().all()
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent

@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db),
                    user: User = Depends(get_current_user)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404)
    return agent

@router.put("/{agent_id}", response_model=AgentRead)
async def update_agent(agent_id: str, body: AgentCreate,
                       db: AsyncSession = Depends(get_db),
                       user: User = Depends(get_current_user)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404)
    agent.name = body.name
    agent.description = body.description
    agent.system_prompt = body.system_prompt
    agent.model = body.model
    await db.commit()
    await db.refresh(agent)
    return agent

@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: str, db: AsyncSession = Depends(get_db),
                       user: User = Depends(get_current_user)):
    # Block deletion if agent is in any team
    membership = await db.execute(select(TeamAgent).where(TeamAgent.agent_id == agent_id))
    if membership.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Agent is a member of a team. Remove it first.")
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404)
    await db.delete(agent)
    await db.commit()
```

- [ ] **Step 5: Run tests — expect pass**

```bash
pytest ../tests/test_agents.py -v
```

- [ ] **Step 6: Commit**

```bash
git add backend/api/agents.py backend/schemas/agent.py tests/test_agents.py
git commit -m "feat: agents CRUD API with pagination"
```

---

### Task 6: Teams CRUD API

**Files:**
- Create: `backend/schemas/team.py`
- Create: `backend/api/teams.py`
- Test: `tests/test_teams.py`

- [ ] **Step 1: Create `backend/schemas/team.py`**

```python
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
    agent: AgentSummary
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
    agents: list[TeamAgentRead]
    model_config = {"from_attributes": True}

class PaginatedTeams(BaseModel):
    items: list[TeamRead]
    total: int
    page: int
    limit: int
```

- [ ] **Step 2: Write failing tests**

```python
# tests/test_teams.py
import pytest

HEADERS = {"X-CCM-User": "alice"}

@pytest.mark.asyncio
async def test_create_and_get_team(client):
    # Create two agents first
    def mk_agent(name):
        return {"name": name, "description": "d", "system_prompt": "s",
                "model": "gpt-4.1", "mcp_tool_ids": [], "skill_ids": []}
    a1 = (await client.post("/api/agents", json=mk_agent("A1"), headers=HEADERS)).json()["id"]
    a2 = (await client.post("/api/agents", json=mk_agent("A2"), headers=HEADERS)).json()["id"]

    payload = {"name": "Credit Team", "description": "d", "mode": "sequential",
               "agents": [{"agent_id": a1, "position": 0}, {"agent_id": a2, "position": 1}]}
    r = await client.post("/api/teams", json=payload, headers=HEADERS)
    assert r.status_code == 201
    team_id = r.json()["id"]

    r = await client.get(f"/api/teams/{team_id}", headers=HEADERS)
    assert r.json()["name"] == "Credit Team"
    assert len(r.json()["agents"]) == 2

@pytest.mark.asyncio
async def test_delete_agent_in_team_returns_409(client):
    payload = {"name": "Solo", "description": "d", "system_prompt": "s",
               "model": "gpt-4.1", "mcp_tool_ids": [], "skill_ids": []}
    agent_id = (await client.post("/api/agents", json=payload, headers=HEADERS)).json()["id"]
    team_payload = {"name": "T", "description": "d", "mode": "sequential",
                    "agents": [{"agent_id": agent_id, "position": 0}]}
    await client.post("/api/teams", json=team_payload, headers=HEADERS)
    r = await client.delete(f"/api/agents/{agent_id}", headers=HEADERS)
    assert r.status_code == 409
```

- [ ] **Step 3: Run — expect failure**

```bash
pytest ../tests/test_teams.py -v
```

- [ ] **Step 4: Implement `backend/api/teams.py`**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.api.deps import get_db, get_current_user
from backend.models.team import Team, TeamAgent
from backend.models.user import User
from backend.schemas.team import TeamCreate, TeamRead, PaginatedTeams

router = APIRouter(prefix="/api/teams", tags=["teams"])

@router.get("", response_model=PaginatedTeams)
async def list_teams(page: int = 1, limit: int = 20,
                     db: AsyncSession = Depends(get_db),
                     user: User = Depends(get_current_user)):
    offset = (page - 1) * limit
    total = (await db.execute(select(func.count(Team.id)))).scalar()
    result = await db.execute(select(Team).offset(offset).limit(limit))
    return PaginatedTeams(items=result.scalars().all(), total=total, page=page, limit=limit)

@router.post("", response_model=TeamRead, status_code=201)
async def create_team(body: TeamCreate, db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)):
    team = Team(name=body.name, description=body.description, mode=body.mode,
                orchestrator_agent_id=body.orchestrator_agent_id,
                loop_max_iterations=body.loop_max_iterations,
                loop_stop_signal=body.loop_stop_signal,
                created_by=user.id)
    db.add(team)
    await db.flush()
    for entry in body.agents:
        db.add(TeamAgent(team_id=team.id, agent_id=entry.agent_id, position=entry.position))
    await db.commit()
    await db.refresh(team)
    return team

@router.get("/{team_id}", response_model=TeamRead)
async def get_team(team_id: str, db: AsyncSession = Depends(get_db),
                   user: User = Depends(get_current_user)):
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404)
    return team

@router.put("/{team_id}", response_model=TeamRead)
async def update_team(team_id: str, body: TeamCreate,
                      db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)):
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404)
    for field in ["name", "description", "mode", "orchestrator_agent_id",
                  "loop_max_iterations", "loop_stop_signal"]:
        setattr(team, field, getattr(body, field))
    # Replace agents
    for ta in team.agents:
        await db.delete(ta)
    await db.flush()
    for entry in body.agents:
        db.add(TeamAgent(team_id=team.id, agent_id=entry.agent_id, position=entry.position))
    await db.commit()
    await db.refresh(team)
    return team

@router.delete("/{team_id}", status_code=204)
async def delete_team(team_id: str, db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)):
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404)
    await db.delete(team)
    await db.commit()
```

- [ ] **Step 5: Register router in `main.py`, run tests**

```python
from backend.api import teams
app.include_router(teams.router)
```

```bash
pytest ../tests/test_teams.py -v
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/api/teams.py backend/schemas/team.py tests/test_teams.py
git commit -m "feat: teams CRUD API with agent ordering and 409 guard"
```

---

### Task 7: Marketplace API

**Files:**
- Create: `backend/schemas/marketplace.py`
- Create: `backend/api/marketplace.py`
- Create: `backend/storage/base.py`
- Create: `backend/storage/local.py`
- Test: `tests/test_marketplace.py`

- [ ] **Step 1: Create storage abstraction**

```python
# backend/storage/base.py
from abc import ABC, abstractmethod

class StorageClient(ABC):
    @abstractmethod
    async def save(self, path: str, data: bytes) -> str:
        """Save data and return the stored path."""

    @abstractmethod
    async def delete(self, path: str) -> None:
        pass
```

```python
# backend/storage/local.py
import os
from backend.storage.base import StorageClient
from backend.config import settings

class LocalStorageClient(StorageClient):
    async def save(self, path: str, data: bytes) -> str:
        full_path = os.path.join(settings.storage_path, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(data)
        return full_path

    async def delete(self, path: str) -> None:
        if os.path.exists(path):
            os.remove(path)

storage = LocalStorageClient()
```

- [ ] **Step 2: Create `backend/schemas/marketplace.py`**

```python
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
```

- [ ] **Step 3: Write failing tests**

```python
# tests/test_marketplace.py
import pytest
import io

HEADERS = {"X-CCM-User": "alice"}
ADMIN_HEADERS = {"X-CCM-User": "admin"}

@pytest.mark.asyncio
async def test_submit_mcp(client, db):
    from backend.models.user import User
    admin = User(username="admin", display_name="Admin", is_admin=True)
    db.add(admin)
    await db.commit()

    r = await client.post("/api/marketplace/submit",
        data={"name": "Company DB", "description": "desc", "type": "mcp",
              "server_url": "http://fake-mcp", "auth_headers": "{}"},
        headers=HEADERS)
    # 400 expected because fake MCP server is unreachable — we test form parsing
    assert r.status_code in (201, 400)

@pytest.mark.asyncio
async def test_list_approved_empty(client):
    r = await client.get("/api/marketplace", headers=HEADERS)
    assert r.status_code == 200
    assert r.json()["items"] == []

@pytest.mark.asyncio
async def test_approve_reject_requires_admin(client):
    r = await client.post("/api/marketplace/fake-id/approve", headers=HEADERS)
    assert r.status_code == 403
```

- [ ] **Step 4: Implement `backend/api/marketplace.py`**

```python
import uuid, json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.api.deps import get_db, get_current_user, get_admin_user
from backend.models.marketplace import MarketplaceItem
from backend.models.user import User
from backend.schemas.marketplace import MarketplaceItemRead, PaginatedMarketplace
from backend.storage.local import storage
from backend.config import settings

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])

@router.get("", response_model=PaginatedMarketplace)
async def list_approved(type: str | None = None, page: int = 1, limit: int = 20,
                         db: AsyncSession = Depends(get_db),
                         user: User = Depends(get_current_user)):
    q = select(MarketplaceItem).where(MarketplaceItem.status == "approved")
    if type:
        q = q.where(MarketplaceItem.type == type)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    result = await db.execute(q.offset((page - 1) * limit).limit(limit))
    return PaginatedMarketplace(items=result.scalars().all(), total=total, page=page, limit=limit)

@router.post("/submit", response_model=MarketplaceItemRead, status_code=201)
async def submit_item(
    name: str = Form(...), description: str = Form(...), type: str = Form(...),
    server_url: str | None = Form(None), auth_headers: str | None = Form(None),
    function_name: str | None = Form(None),
    input_schema: str | None = Form(None), output_schema: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    if type == "mcp":
        config = {"server_url": server_url,
                  "auth_headers": json.loads(auth_headers or "{}")}
        # Attempt tool discovery
        discovered = await _discover_mcp_tools(server_url, json.loads(auth_headers or "{}"))
        item = MarketplaceItem(name=name, description=description, type="mcp",
                               config=config, submitted_by=user.id,
                               discovered_tools=discovered)
    elif type == "skill":
        if not file:
            raise HTTPException(status_code=400, detail="Skill requires a .py file")
        file_content = await file.read()
        path = f"skills/{uuid.uuid4()}_{file.filename}"
        stored_path = await storage.save(path, file_content)
        config = {"function_name": function_name,
                  "input_schema": json.loads(input_schema or "{}"),
                  "output_schema": json.loads(output_schema or "{}")}
        item = MarketplaceItem(name=name, description=description, type="skill",
                               config=config, file_path=stored_path, submitted_by=user.id)
    else:
        raise HTTPException(status_code=400, detail="type must be mcp or skill")
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item

async def _discover_mcp_tools(server_url: str, headers: dict) -> list[str]:
    try:
        from agent_framework import MCPStreamableHTTPTool
        tool = MCPStreamableHTTPTool(name="discovery", url=server_url, headers=headers,
                                     load_prompts=False)
        async with tool:
            return [f.name for f in tool.functions] if tool.functions else []
    except Exception as e:
        # Spec: if the backend can't reach/discover the MCP server, reject submission with 400.
        raise HTTPException(status_code=400, detail="Could not connect to MCP server")

@router.get("/pending", response_model=PaginatedMarketplace)
async def list_pending(page: int = 1, limit: int = 20,
                       db: AsyncSession = Depends(get_db),
                       admin: User = Depends(get_admin_user)):
    q = select(MarketplaceItem).where(MarketplaceItem.status == "pending")
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    result = await db.execute(q.offset((page - 1) * limit).limit(limit))
    return PaginatedMarketplace(items=result.scalars().all(), total=total, page=page, limit=limit)

@router.post("/{item_id}/approve", response_model=MarketplaceItemRead)
async def approve_item(item_id: str, db: AsyncSession = Depends(get_db),
                       admin: User = Depends(get_admin_user)):
    return await _set_status(item_id, "approved", admin.id, db)

@router.post("/{item_id}/reject", response_model=MarketplaceItemRead)
async def reject_item(item_id: str, db: AsyncSession = Depends(get_db),
                      admin: User = Depends(get_admin_user)):
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
```

- [ ] **Step 5: Register router, run tests**

```python
from backend.api import marketplace
app.include_router(marketplace.router)
```

```bash
pytest ../tests/test_marketplace.py -v
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/api/marketplace.py backend/schemas/marketplace.py backend/storage/ tests/test_marketplace.py
git commit -m "feat: marketplace API with MCP auto-discovery and skill file upload"
```

---

### Task 8: Conversations API and file upload

**Files:**
- Create: `backend/schemas/conversation.py`
- Create: `backend/api/conversations.py`
- Create: `backend/core/file_extractor.py`
- Test: `tests/test_conversations.py`

- [ ] **Step 1: Create `backend/core/file_extractor.py`**

```python
import io
from pathlib import Path

def extract_text(filename: str, data: bytes) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
    elif ext in (".xlsx", ".xls"):
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(data), read_only=True)
        rows = []
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                rows.append(" | ".join(str(c) for c in row if c is not None))
        return "\n".join(rows)
    elif ext in (".docx", ".doc"):
        from docx import Document
        doc = Document(io.BytesIO(data))
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError(f"Unsupported file type: {ext}")
```

- [ ] **Step 2: Write failing tests**

```python
# tests/test_conversations.py
import pytest

HEADERS = {"X-CCM-User": "alice"}

@pytest.mark.asyncio
async def test_create_and_list_conversations(client):
    # Need an agent first
    agent_payload = {"name": "Bot", "description": "d", "system_prompt": "s",
                     "model": "gpt-4.1", "mcp_tool_ids": [], "skill_ids": []}
    agent_id = (await client.post("/api/agents", json=agent_payload, headers=HEADERS)).json()["id"]

    r = await client.post("/api/conversations",
        json={"title": "Q1 Analysis", "target_type": "agent", "target_id": agent_id},
        headers=HEADERS)
    assert r.status_code == 201
    conv_id = r.json()["id"]

    r = await client.get("/api/conversations", headers=HEADERS)
    assert any(c["id"] == conv_id for c in r.json()["items"])

@pytest.mark.asyncio
async def test_delete_conversation(client):
    agent_id = (await client.post("/api/agents",
        json={"name": "B", "description": "d", "system_prompt": "s",
              "model": "gpt-4.1", "mcp_tool_ids": [], "skill_ids": []},
        headers=HEADERS)).json()["id"]
    conv_id = (await client.post("/api/conversations",
        json={"title": "t", "target_type": "agent", "target_id": agent_id},
        headers=HEADERS)).json()["id"]
    r = await client.delete(f"/api/conversations/{conv_id}", headers=HEADERS)
    assert r.status_code == 204
```

- [ ] **Step 3: Implement `backend/api/conversations.py`** (CRUD only, no chat yet)

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.api.deps import get_db, get_current_user
from backend.models.conversation import Conversation, Message, Attachment
from backend.models.user import User

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

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

@router.get("", response_model=PaginatedConversations)
async def list_conversations(page: int = 1, limit: int = 20,
                              db: AsyncSession = Depends(get_db),
                              user: User = Depends(get_current_user)):
    q = select(Conversation).where(Conversation.created_by == user.id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    result = await db.execute(q.offset((page - 1) * limit).limit(limit))
    return PaginatedConversations(items=result.scalars().all(), total=total, page=page, limit=limit)

@router.post("", response_model=ConversationRead, status_code=201)
async def create_conversation(body: ConversationCreate,
                               db: AsyncSession = Depends(get_db),
                               user: User = Depends(get_current_user)):
    conv = Conversation(title=body.title, target_type=body.target_type,
                        target_id=body.target_id, created_by=user.id)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv

@router.get("/{conv_id}")
async def get_conversation(conv_id: str, db: AsyncSession = Depends(get_db),
                            user: User = Depends(get_current_user)):
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404)
    return conv

@router.delete("/{conv_id}", status_code=204)
async def delete_conversation(conv_id: str, db: AsyncSession = Depends(get_db),
                               user: User = Depends(get_current_user)):
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404)
    # Delete stored files
    for att in conv.attachments:
        import os
        if os.path.exists(att.file_path):
            os.remove(att.file_path)
    await db.delete(conv)
    await db.commit()
```

- [ ] **Step 4: Register router, run tests**

```python
from backend.api import conversations
app.include_router(conversations.router)
```

```bash
pytest ../tests/test_conversations.py -v
```
Expected: PASS

- [ ] **Step 5: Add file upload endpoint to `conversations.py`**

```python
import uuid
from fastapi import UploadFile, File
from backend.core.file_extractor import extract_text
from backend.storage.local import storage

ALLOWED_MIME = {"application/pdf", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/msword"}
MAX_SIZE = 20 * 1024 * 1024  # 20MB

@router.post("/{conv_id}/upload")
async def upload_file(conv_id: str, file: UploadFile = File(...),
                      db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)):
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

    att = Attachment(conversation_id=conv_id, filename=file.filename,
                     file_path=stored, mime_type=file.content_type or "",
                     size=len(data), extracted_text=text)
    db.add(att)
    await db.commit()
    await db.refresh(att)
    return {"attachment_id": att.id, "filename": att.filename,
            "mime_type": att.mime_type, "size": att.size,
            "extracted_text_preview": text[:500]}
```

- [ ] **Step 6: Commit**

```bash
git add backend/api/conversations.py backend/core/file_extractor.py tests/test_conversations.py
git commit -m "feat: conversations API and file upload with text extraction"
```

---

## Phase 4: Agent Execution Engine

### Task 9: Skill runner

**Files:**
- Create: `backend/core/skill_runner.py`
- Test: `tests/test_skill_runner.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_skill_runner.py
import pytest
import textwrap
import tempfile, os
from backend.core.skill_runner import run_skill

@pytest.mark.asyncio
async def test_skill_returns_result(tmp_path):
    skill_file = tmp_path / "my_skill.py"
    skill_file.write_text(textwrap.dedent("""
        def add_numbers(a: int, b: int) -> int:
            return a + b
    """))
    result = await run_skill(str(skill_file), "add_numbers", {"a": 3, "b": 4})
    assert result == 7

@pytest.mark.asyncio
async def test_skill_timeout(tmp_path):
    skill_file = tmp_path / "slow.py"
    skill_file.write_text(textwrap.dedent("""
        import time
        def slow():
            time.sleep(60)
    """))
    result = await run_skill(str(skill_file), "slow", {}, timeout=1)
    assert "error" in result

@pytest.mark.asyncio
async def test_skill_exception(tmp_path):
    skill_file = tmp_path / "bad.py"
    skill_file.write_text("def boom(): raise ValueError('oops')")
    result = await run_skill(str(skill_file), "boom", {})
    assert "error" in result
```

- [ ] **Step 2: Run — expect failure**

```bash
pytest ../tests/test_skill_runner.py -v
```

- [ ] **Step 3: Implement `backend/core/skill_runner.py`**

```python
import asyncio
import json
import sys
from typing import Any

RUNNER_SCRIPT = """
import sys, json, importlib.util

payload = json.loads(sys.stdin.read())
spec = importlib.util.spec_from_file_location("skill", payload["file_path"])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
fn = getattr(module, payload["function_name"])
result = fn(**payload["args"])
print(json.dumps(result))
"""

async def run_skill(file_path: str, function_name: str,
                    args: dict, timeout: int = 30) -> Any:
    payload = json.dumps({"file_path": file_path, "function_name": function_name, "args": args})
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-c", RUNNER_SCRIPT,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(payload.encode()), timeout=timeout
        )
        if proc.returncode != 0:
            return {"error": "skill_error", "message": stderr.decode()[:500]}
        return json.loads(stdout.decode())
    except asyncio.TimeoutError:
        proc.kill()
        return {"error": "skill_timeout", "message": f"Skill exceeded {timeout}s timeout"}
    except Exception as e:
        return {"error": "skill_error", "message": str(e)}
```

- [ ] **Step 4: Run tests — expect pass**

```bash
pytest ../tests/test_skill_runner.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/core/skill_runner.py tests/test_skill_runner.py
git commit -m "feat: sandboxed skill runner via subprocess with timeout"
```

---

### Task 10: Single agent runner with SSE streaming

**Files:**
- Create: `backend/core/agent_runner.py`
- Modify: `backend/api/conversations.py` (add `/chat` endpoint)
- Test: `tests/test_agent_runner.py`

- [ ] **Step 1: Write failing test for agent runner**

```python
# tests/test_agent_runner.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_agent_runner_streams_tokens():
    """Agent runner yields SSE events for a simple response."""
    from backend.core.agent_runner import run_agent_stream

    mock_agent_db = MagicMock()
    mock_agent_db.system_prompt = "You are helpful."
    mock_agent_db.model = "gpt-4.1"
    mock_agent_db.mcp_tools = []
    mock_agent_db.skills = []

    events = []
    with patch("backend.core.agent_runner.ChatAgent") as MockChatAgent:
        mock_instance = AsyncMock()
        mock_instance.run = AsyncMock(return_value=MagicMock(content="Hello!"))
        MockChatAgent.return_value = mock_instance

        async for event in run_agent_stream(mock_agent_db, "Hi", [], []):
            events.append(event)

    event_types = [e["event"] for e in events]
    assert "step_start" in event_types
    assert "done" in event_types
```

- [ ] **Step 2: Run — expect failure**

```bash
pytest ../tests/test_agent_runner.py -v
```

- [ ] **Step 3: Implement `backend/core/agent_runner.py`**

```python
import json
from typing import AsyncGenerator, Any
from backend.config import settings
from backend.core.skill_runner import run_skill

def _sse(event: str, data: dict) -> dict:
    return {"event": event, "data": data}

async def run_agent_stream(
    agent_db,
    message: str,
    history: list[dict],
    attachments: list,
) -> AsyncGenerator[dict, None]:
    from agent_framework import ChatAgent
    from agent_framework.clients.azure import AzureOpenAIChatClient

    yield _sse("step_start", {"step": 1, "agent_name": agent_db.name})

    try:
        client = AzureOpenAIChatClient(
            endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            deployment_name=agent_db.model,
        )

        tools = []

        # MCP tools
        for mcp in agent_db.mcp_tools:
            from agent_framework import MCPStreamableHTTPTool
            tools.append(MCPStreamableHTTPTool(
                name=mcp.name,
                url=mcp.config["server_url"],
                headers=mcp.config.get("auth_headers", {}),
            ))

        # Skills as AI functions
        for skill in agent_db.skills:
            from agent_framework.functions import AIFunction
            import functools

            async def _invoke(skill_item=skill, **kwargs):
                return await run_skill(
                    skill_item.file_path,
                    skill_item.config["function_name"],
                    kwargs,
                )

            fn = AIFunction(
                name=skill.name,
                description=skill.description,
                fn=_invoke,
                parameters=skill.config.get("input_schema", {}),
            )
            tools.append(fn)

        # Build context
        file_context = ""
        for att in attachments:
            file_context += f"\n--- File: {att.filename} ---\n{att.extracted_text}\n---\n"

        full_message = f"{file_context}\n{message}".strip() if file_context else message

        chat_agent = ChatAgent(
            chat_client=client,
            instructions=agent_db.system_prompt,
            tools=tools if tools else None,
        )

        # Stream response
        async with chat_agent:
            response = await chat_agent.run(full_message)
            # Emit content as tokens
            if hasattr(response, "content"):
                for chunk in _chunk_text(response.content):
                    yield _sse("token", {"text": chunk})
            yield _sse("step_end", {"step": 1, "agent_name": agent_db.name})

    except Exception as e:
        yield _sse("error", {"code": "azure_error", "message": str(e)})
        return

def _chunk_text(text: str, size: int = 20) -> list[str]:
    """Split text into chunks to simulate streaming."""
    return [text[i:i+size] for i in range(0, len(text), size)]
```

> **Note:** `agent-framework==1.0.0rc4` import paths (`AzureOpenAIChatClient`, `AIFunction`) should be verified against the installed package. Run `python -c "import agent_framework; help(agent_framework)"` to confirm exact names.

- [ ] **Step 4: Add `/chat` SSE endpoint to `conversations.py`**

```python
from fastapi import Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    attachment_ids: list[str] = []

@router.post("/{conv_id}/chat")
async def chat(conv_id: str, body: ChatRequest, request: Request,
               db: AsyncSession = Depends(get_db),
               user: User = Depends(get_current_user)):
    result = await db.execute(select(Conversation).where(Conversation.id == conv_id))
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404)

    # Fetch history
    history = [{"role": m.role, "content": m.content} for m in conv.messages[-20:]]

    # Fetch attachments
    attachments = []
    if body.attachment_ids:
        att_result = await db.execute(
            select(Attachment).where(Attachment.id.in_(body.attachment_ids)))
        attachments = att_result.scalars().all()

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
    user_msg = Message(conversation_id=conv_id, role="user",
                       content={"text": body.message})
    db.add(user_msg)
    await db.commit()

    # Link attachments to message
    for att in attachments:
        att.message_id = user_msg.id
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
            asst_msg = Message(conversation_id=conv_id, role="assistant",
                               content={"text": "".join(full_response),
                                        "agent_name": getattr(agent_db, "name", "")})
            db.add(asst_msg)
            await db.commit()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

- [ ] **Step 5: Run tests**

```bash
pytest ../tests/test_agent_runner.py -v
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/core/agent_runner.py tests/test_agent_runner.py backend/api/conversations.py
git commit -m "feat: single agent SSE streaming via agent-framework ChatAgent"
```

---

### Task 11: Team runner (sequential, orchestrator, loop)

**Files:**
- Create: `backend/core/team_runner.py`
- Test: `tests/test_team_runner.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_team_runner.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

def make_agent(name):
    a = MagicMock()
    a.name = name
    a.system_prompt = f"You are {name}."
    a.model = "gpt-4.1"
    a.mcp_tools = []
    a.skills = []
    return a

def make_team_agent(agent, position):
    ta = MagicMock()
    ta.agent = agent
    ta.position = position
    return ta

@pytest.mark.asyncio
async def test_sequential_emits_steps():
    from backend.core.team_runner import run_team_stream
    team = MagicMock()
    team.mode = "sequential"
    team.agents = [make_team_agent(make_agent("A1"), 0),
                   make_team_agent(make_agent("A2"), 1)]

    with patch("backend.core.team_runner.run_agent_stream") as mock_stream:
        async def fake_stream(agent, message, history, attachments):
            yield {"event": "step_start", "data": {"step": 1, "agent_name": agent.name}}
            yield {"event": "token", "data": {"text": f"output from {agent.name}"}}
            yield {"event": "step_end", "data": {"step": 1, "agent_name": agent.name}}
            yield {"event": "done", "data": {"message_id": "x"}}
        mock_stream.side_effect = fake_stream

        events = [e async for e in run_team_stream(team, "hello", [], [])]

    step_starts = [e for e in events if e["event"] == "step_start"]
    assert len(step_starts) == 2  # one per agent

@pytest.mark.asyncio
async def test_loop_stops_at_max_iterations():
    from backend.core.team_runner import run_team_stream
    team = MagicMock()
    team.mode = "loop"
    team.loop_max_iterations = 2
    team.loop_stop_signal = None
    team.agents = [make_team_agent(make_agent("A"), 0)]

    with patch("backend.core.team_runner.run_agent_stream") as mock_stream:
        async def fake_stream(agent, message, history, attachments):
            yield {"event": "token", "data": {"text": "result"}}
            yield {"event": "done", "data": {"message_id": "x"}}
        mock_stream.side_effect = fake_stream

        events = [e async for e in run_team_stream(team, "hello", [], [])]

    done_events = [e for e in events if e["event"] == "done"]
    assert len(done_events) == 1
```

- [ ] **Step 2: Run — expect failure**

```bash
pytest ../tests/test_team_runner.py -v
```

- [ ] **Step 3: Implement `backend/core/team_runner.py`**

```python
from typing import AsyncGenerator
from backend.core.agent_runner import run_agent_stream, _sse

async def run_team_stream(team_db, message: str, history: list, attachments: list) -> AsyncGenerator[dict, None]:
    if team_db.mode == "sequential":
        async for event in _sequential(team_db, message, history, attachments):
            yield event
    elif team_db.mode == "orchestrator":
        async for event in _orchestrator(team_db, message, history, attachments):
            yield event
    elif team_db.mode == "loop":
        async for event in _loop(team_db, message, history, attachments):
            yield event

async def _sequential(team_db, message, history, attachments):
    current_input = message
    agents = sorted(team_db.agents, key=lambda ta: ta.position)
    step = 0
    for i, team_agent in enumerate(agents):
        step += 1
        agent = team_agent.agent
        is_last = i == len(agents) - 1
        output_tokens = []

        async for event in run_agent_stream(agent, current_input, history, attachments if i == 0 else []):
            if is_last:
                yield event  # stream final agent's tokens to user
            else:
                # Intermediate: only emit step markers, buffer output
                if event["event"] in ("step_start", "step_end"):
                    yield event
                elif event["event"] == "token":
                    output_tokens.append(event["data"]["text"])
                elif event["event"] == "error":
                    yield event
                    return

        current_input = "".join(output_tokens) if not is_last else current_input

async def _orchestrator(team_db, message, history, attachments):
    from backend.models.agent import Agent as AgentModel
    from sqlalchemy.ext.asyncio import AsyncSession

    # Find lead agent
    lead_ta = next((ta for ta in team_db.agents
                    if ta.agent_id == team_db.orchestrator_agent_id), team_db.agents[0])
    specialists = [ta.agent for ta in team_db.agents if ta.agent_id != lead_ta.agent_id]

    # Stream lead agent (it calls specialists as tools via agent-framework's orchestration)
    # For simplicity: lead agent gets specialist descriptions injected into its system prompt
    specialist_info = "\n".join(
        f"- {s.name}: {s.description}" for s in specialists
    )
    lead_agent = lead_ta.agent
    augmented_prompt = (f"{lead_agent.system_prompt}\n\n"
                        f"You can delegate to these specialists:\n{specialist_info}\n"
                        f"When you need a specialist, say 'DELEGATE TO <name>: <task>'.")

    patched_agent = _patch_prompt(lead_agent, augmented_prompt)
    step = 1
    yield _sse("step_start", {"step": step, "agent_name": lead_agent.name})
    output = []
    async for event in run_agent_stream(patched_agent, message, history, attachments):
        if event["event"] == "token":
            output.append(event["data"]["text"])
            yield event
        elif event["event"] in ("step_end", "done", "error"):
            yield event

def _patch_prompt(agent, new_prompt):
    """Return a copy of agent with a different system prompt (no DB write)."""
    from types import SimpleNamespace
    return SimpleNamespace(
        name=agent.name, system_prompt=new_prompt,
        model=agent.model, mcp_tools=agent.mcp_tools, skills=agent.skills
    )

async def _loop(team_db, message, history, attachments):
    max_iter = team_db.loop_max_iterations or 5
    stop_signal = team_db.loop_stop_signal
    agents = sorted(team_db.agents, key=lambda ta: ta.position)
    current_input = message

    for iteration in range(max_iter):
        step_offset = iteration * len(agents)
        last_output = []

        for i, team_agent in enumerate(agents):
            is_last_agent = i == len(agents) - 1
            is_last_iter = iteration == max_iter - 1
            stream_tokens = is_last_agent and is_last_iter
            agent = team_agent.agent
            step = step_offset + i + 1

            yield _sse("step_start", {"step": step, "agent_name": agent.name})
            agent_output = []
            async for event in run_agent_stream(agent, current_input, history, attachments if iteration == 0 and i == 0 else []):
                if event["event"] == "token":
                    agent_output.append(event["data"]["text"])
                    if stream_tokens:
                        yield event
                elif event["event"] in ("step_end", "error"):
                    yield event
            yield _sse("step_end", {"step": step, "agent_name": agent.name})

            if is_last_agent:
                last_output = agent_output
                current_input = "".join(agent_output)

        # Check stop signal after full iteration
        full_output = "".join(last_output)
        if stop_signal and stop_signal.lower() in full_output.lower():
            break

    yield _sse("done", {"message_id": ""})
```

- [ ] **Step 4: Run tests**

```bash
pytest ../tests/test_team_runner.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/core/team_runner.py tests/test_team_runner.py
git commit -m "feat: team runner with sequential, orchestrator, and loop modes"
```

---

## Phase 5: Frontend

### Task 12: Hub page — browse agents, teams, MCPs, skills

**Files:**
- Create: `frontend/src/api/agents.ts`
- Create: `frontend/src/api/teams.ts`
- Create: `frontend/src/api/marketplace.ts`
- Create: `frontend/src/components/ItemCard.tsx`
- Create: `frontend/src/pages/Hub/index.tsx`

- [ ] **Step 1: Create API client modules**

```typescript
// frontend/src/api/agents.ts
import client from './client'

export const getAgents = (page = 1) =>
  client.get('/api/agents', { params: { page, limit: 20 } }).then(r => r.data)

export const createAgent = (data: any) =>
  client.post('/api/agents', data).then(r => r.data)

export const updateAgent = (id: string, data: any) =>
  client.put(`/api/agents/${id}`, data).then(r => r.data)

export const deleteAgent = (id: string) =>
  client.delete(`/api/agents/${id}`)
```

```typescript
// frontend/src/api/teams.ts
import client from './client'

export const getTeams = (page = 1) =>
  client.get('/api/teams', { params: { page, limit: 20 } }).then(r => r.data)

export const createTeam = (data: any) =>
  client.post('/api/teams', data).then(r => r.data)

export const deleteTeam = (id: string) =>
  client.delete(`/api/teams/${id}`)
```

```typescript
// frontend/src/api/marketplace.ts
import client from './client'

export const getMarketplace = (type?: string, page = 1) =>
  client.get('/api/marketplace', { params: { type, page, limit: 20 } }).then(r => r.data)

export const submitMCP = (data: FormData) =>
  client.post('/api/marketplace/submit', data).then(r => r.data)

export const submitSkill = (data: FormData) =>
  client.post('/api/marketplace/submit', data).then(r => r.data)
```

- [ ] **Step 2: Create `frontend/src/components/ItemCard.tsx`**

```typescript
interface ItemCardProps {
  name: string
  description: string
  type: 'agent' | 'team' | 'mcp' | 'skill'
  status?: string
  creator?: string
  onUse?: () => void
  onEdit?: () => void
  onDelete?: () => void
}

export default function ItemCard({ name, description, type, status, creator, onUse, onEdit, onDelete }: ItemCardProps) {
  const typeColors = { agent: 'blue', team: 'purple', mcp: 'green', skill: 'orange' }
  const color = typeColors[type]

  return (
    <div className="border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow bg-white">
      <div className="flex items-start justify-between mb-2">
        <span className={`text-xs font-medium px-2 py-1 rounded bg-${color}-100 text-${color}-700`}>
          {type.toUpperCase()}
        </span>
        {status && (
          <span className={`text-xs px-2 py-1 rounded ${status === 'approved' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
            {status}
          </span>
        )}
      </div>
      <h3 className="font-semibold text-gray-900 mt-2">{name}</h3>
      <p className="text-sm text-gray-500 mt-1 line-clamp-2">{description}</p>
      {creator && <p className="text-xs text-gray-400 mt-2">by {creator}</p>}
      <div className="flex gap-2 mt-3">
        {onUse && (
          <button onClick={onUse}
            className="flex-1 text-sm bg-blue-600 text-white px-3 py-1.5 rounded hover:bg-blue-700">
            Use in Playground
          </button>
        )}
        {onEdit && (
          <button onClick={onEdit}
            className="text-sm border px-3 py-1.5 rounded hover:bg-gray-50">
            Edit
          </button>
        )}
        {onDelete && (
          <button onClick={onDelete}
            className="text-sm text-red-600 border border-red-200 px-3 py-1.5 rounded hover:bg-red-50">
            Delete
          </button>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Create `frontend/src/pages/Hub/index.tsx`**

```typescript
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getAgents } from '../../api/agents'
import { getTeams } from '../../api/teams'
import { getMarketplace } from '../../api/marketplace'
import ItemCard from '../../components/ItemCard'

type Tab = 'agents' | 'teams' | 'mcp' | 'skills'

export default function Hub() {
  const [tab, setTab] = useState<Tab>('agents')
  const navigate = useNavigate()

  const { data: agents } = useQuery({ queryKey: ['agents'], queryFn: () => getAgents() })
  const { data: teams } = useQuery({ queryKey: ['teams'], queryFn: () => getTeams() })
  const { data: mcps } = useQuery({ queryKey: ['marketplace', 'mcp'], queryFn: () => getMarketplace('mcp') })
  const { data: skills } = useQuery({ queryKey: ['marketplace', 'skill'], queryFn: () => getMarketplace('skill') })

  const tabs: { key: Tab; label: string }[] = [
    { key: 'agents', label: 'Agents' },
    { key: 'teams', label: 'Teams' },
    { key: 'mcp', label: 'MCP Tools' },
    { key: 'skills', label: 'Skills' },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">CCM Agent Hub</h1>
        <div className="flex gap-2">
          <button onClick={() => navigate('/builder/agent')}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm">
            + New Agent
          </button>
          <button onClick={() => navigate('/builder/team')}
            className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 text-sm">
            + New Team
          </button>
        </div>
      </div>

      <div className="flex border-b mb-6">
        {tabs.map(t => (
          <button key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t.key ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {tab === 'agents' && agents?.items?.map((a: any) => (
          <ItemCard key={a.id} name={a.name} description={a.description} type="agent"
            creator={a.created_by}
            onUse={() => navigate(`/playground/agent/${a.id}`)}
            onEdit={() => navigate(`/builder/agent?id=${a.id}`)} />
        ))}
        {tab === 'teams' && teams?.items?.map((t: any) => (
          <ItemCard key={t.id} name={t.name} description={t.description} type="team"
            creator={t.created_by}
            onUse={() => navigate(`/playground/team/${t.id}`)} />
        ))}
        {tab === 'mcp' && mcps?.items?.map((m: any) => (
          <ItemCard key={m.id} name={m.name} description={m.description} type="mcp"
            status={m.status} creator={m.submitted_by} />
        ))}
        {tab === 'skills' && skills?.items?.map((s: any) => (
          <ItemCard key={s.id} name={s.name} description={s.description} type="skill"
            status={s.status} creator={s.submitted_by} />
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Update `App.tsx` to use Hub**

```typescript
import Hub from './pages/Hub'
// Replace placeholder <div>Hub coming soon</div> with <Hub />
```

- [ ] **Step 5: Verify in browser — hub renders with tabs**

```bash
cd frontend && npm run dev
```
Navigate to `http://localhost:5173` — should see Hub with tabs.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/
git commit -m "feat: Hub page with tabbed browse grid for agents, teams, MCPs, skills"
```

---

### Task 13: Agent Builder

**Files:**
- Create: `frontend/src/pages/Builder/AgentBuilder.tsx`
- Create: `frontend/src/api/conversations.ts`

- [ ] **Step 1: Create `frontend/src/api/conversations.ts`**

```typescript
import client from './client'

export const getConversations = () =>
  client.get('/api/conversations').then(r => r.data)

export const createConversation = (data: { title: string; target_type: string; target_id: string }) =>
  client.post('/api/conversations', data).then(r => r.data)

export const uploadFile = (convId: string, file: File) => {
  const form = new FormData()
  form.append('file', file)
  return client.post(`/api/conversations/${convId}/upload`, form).then(r => r.data)
}
```

- [ ] **Step 2: Create `frontend/src/pages/Builder/AgentBuilder.tsx`**

```typescript
import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMarketplace } from '../../api/marketplace'
import { createAgent, updateAgent } from '../../api/agents'
import client from '../../api/client'

const MODELS = ['gpt-4.1-mini', 'gpt-4.1', 'gpt-5', 'gpt-5.1']

export default function AgentBuilder() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const agentId = params.get('id')
  const qc = useQueryClient()

  const [form, setForm] = useState({
    name: '', description: '', system_prompt: '', model: 'gpt-4.1',
    mcp_tool_ids: [] as string[], skill_ids: [] as string[],
  })

  const { data: mcps } = useQuery({ queryKey: ['marketplace', 'mcp'], queryFn: () => getMarketplace('mcp') })
  const { data: skills } = useQuery({ queryKey: ['marketplace', 'skill'], queryFn: () => getMarketplace('skill') })

  useEffect(() => {
    if (agentId) {
      client.get(`/api/agents/${agentId}`).then(r => {
        const a = r.data
        setForm({ name: a.name, description: a.description, system_prompt: a.system_prompt,
                  model: a.model, mcp_tool_ids: a.mcp_tools.map((m: any) => m.id),
                  skill_ids: a.skills.map((s: any) => s.id) })
      })
    }
  }, [agentId])

  const save = useMutation({
    mutationFn: () => agentId ? updateAgent(agentId, form) : createAgent(form),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['agents'] }); navigate('/') },
  })

  const toggle = (field: 'mcp_tool_ids' | 'skill_ids', id: string) => {
    setForm(f => ({
      ...f,
      [field]: f[field].includes(id) ? f[field].filter(x => x !== id) : [...f[field], id],
    }))
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-xl font-bold mb-6">{agentId ? 'Edit Agent' : 'New Agent'}</h1>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
          <input className="w-full border rounded px-3 py-2 text-sm"
            value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <input className="w-full border rounded px-3 py-2 text-sm"
            value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">System Prompt</label>
          <textarea rows={6} className="w-full border rounded px-3 py-2 text-sm font-mono"
            value={form.system_prompt}
            onChange={e => setForm(f => ({ ...f, system_prompt: e.target.value }))} />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
          <select className="w-full border rounded px-3 py-2 text-sm"
            value={form.model} onChange={e => setForm(f => ({ ...f, model: e.target.value }))}>
            {MODELS.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">MCP Tools</label>
          <div className="space-y-1 max-h-40 overflow-y-auto border rounded p-2">
            {mcps?.items?.length === 0 && <p className="text-xs text-gray-400">No approved MCP tools yet</p>}
            {mcps?.items?.map((m: any) => (
              <label key={m.id} className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="checkbox" checked={form.mcp_tool_ids.includes(m.id)}
                  onChange={() => toggle('mcp_tool_ids', m.id)} />
                <span>{m.name}</span>
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Skills</label>
          <div className="space-y-1 max-h-40 overflow-y-auto border rounded p-2">
            {skills?.items?.length === 0 && <p className="text-xs text-gray-400">No approved skills yet</p>}
            {skills?.items?.map((s: any) => (
              <label key={s.id} className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="checkbox" checked={form.skill_ids.includes(s.id)}
                  onChange={() => toggle('skill_ids', s.id)} />
                <span>{s.name}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="flex gap-3 pt-2">
          <button onClick={() => save.mutate()}
            disabled={save.isPending}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 text-sm disabled:opacity-50">
            {save.isPending ? 'Saving...' : 'Save Agent'}
          </button>
          <button onClick={() => navigate('/')}
            className="border px-6 py-2 rounded hover:bg-gray-50 text-sm">
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Wire into `App.tsx`**

```typescript
import AgentBuilder from './pages/Builder/AgentBuilder'
// Replace <div>Agent Builder coming soon</div> with <AgentBuilder />
```

- [ ] **Step 4: Verify in browser — agent builder renders and saves**

- [ ] **Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: no-code agent builder with model, MCP, and skill selection"
```

---

### Task 14: Team Builder

**Files:**
- Create: `frontend/src/pages/Builder/TeamBuilder.tsx`

- [ ] **Step 1: Create `frontend/src/pages/Builder/TeamBuilder.tsx`**

```typescript
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getAgents } from '../../api/agents'
import { createTeam } from '../../api/teams'

type Mode = 'sequential' | 'orchestrator' | 'loop'

export default function TeamBuilder() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [form, setForm] = useState({
    name: '', description: '', mode: 'sequential' as Mode,
    selectedAgentIds: [] as string[],
    orchestrator_agent_id: null as string | null,
    loop_max_iterations: 5, loop_stop_signal: '',
  })

  const { data: agents } = useQuery({ queryKey: ['agents'], queryFn: () => getAgents() })

  const save = useMutation({
    mutationFn: () => createTeam({
      name: form.name,
      description: form.description,
      mode: form.mode,
      agents: form.selectedAgentIds.map((id, i) => ({ agent_id: id, position: i })),
      orchestrator_agent_id: form.mode === 'orchestrator' ? form.orchestrator_agent_id : null,
      loop_max_iterations: form.mode === 'loop' ? form.loop_max_iterations : null,
      loop_stop_signal: form.mode === 'loop' && form.loop_stop_signal ? form.loop_stop_signal : null,
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['teams'] }); navigate('/') },
  })

  const toggleAgent = (id: string) => {
    setForm(f => ({
      ...f,
      selectedAgentIds: f.selectedAgentIds.includes(id)
        ? f.selectedAgentIds.filter(x => x !== id)
        : [...f.selectedAgentIds, id],
    }))
  }

  const selectedAgents = agents?.items?.filter((a: any) => form.selectedAgentIds.includes(a.id)) ?? []

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-xl font-bold mb-6">New Team</h1>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
          <input className="w-full border rounded px-3 py-2 text-sm"
            value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <input className="w-full border rounded px-3 py-2 text-sm"
            value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Collaboration Mode</label>
          <div className="grid grid-cols-3 gap-3">
            {(['sequential', 'orchestrator', 'loop'] as Mode[]).map(m => (
              <button key={m} onClick={() => setForm(f => ({ ...f, mode: m }))}
                className={`border rounded p-3 text-sm text-left transition-colors ${
                  form.mode === m ? 'border-blue-600 bg-blue-50 text-blue-700' : 'hover:bg-gray-50'
                }`}>
                <div className="font-medium capitalize">{m}</div>
                <div className="text-xs text-gray-500 mt-1">
                  {m === 'sequential' && 'Agents run in order'}
                  {m === 'orchestrator' && 'Lead agent routes tasks'}
                  {m === 'loop' && 'Agents cycle until done'}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Select Agents {form.selectedAgentIds.length > 0 && `(${form.selectedAgentIds.length} selected)`}
          </label>
          <div className="space-y-1 max-h-48 overflow-y-auto border rounded p-2">
            {agents?.items?.map((a: any) => (
              <label key={a.id} className="flex items-center gap-2 text-sm cursor-pointer p-1 hover:bg-gray-50 rounded">
                <input type="checkbox" checked={form.selectedAgentIds.includes(a.id)}
                  onChange={() => toggleAgent(a.id)} />
                <span className="font-medium">{a.name}</span>
                <span className="text-gray-400 text-xs">{a.model}</span>
              </label>
            ))}
          </div>
        </div>

        {form.mode === 'orchestrator' && selectedAgents.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Lead Agent (Orchestrator)</label>
            <select className="w-full border rounded px-3 py-2 text-sm"
              value={form.orchestrator_agent_id || ''}
              onChange={e => setForm(f => ({ ...f, orchestrator_agent_id: e.target.value }))}>
              <option value="">Select lead agent...</option>
              {selectedAgents.map((a: any) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </div>
        )}

        {form.mode === 'loop' && (
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Max Iterations</label>
              <input type="number" min={1} max={20} className="w-full border rounded px-3 py-2 text-sm"
                value={form.loop_max_iterations}
                onChange={e => setForm(f => ({ ...f, loop_max_iterations: +e.target.value }))} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Stop Signal <span className="text-gray-400 font-normal">(optional keyword to stop early)</span>
              </label>
              <input className="w-full border rounded px-3 py-2 text-sm"
                placeholder="e.g. APPROVED"
                value={form.loop_stop_signal}
                onChange={e => setForm(f => ({ ...f, loop_stop_signal: e.target.value }))} />
            </div>
          </div>
        )}

        <div className="flex gap-3 pt-2">
          <button onClick={() => save.mutate()}
            disabled={save.isPending || form.selectedAgentIds.length === 0}
            className="bg-purple-600 text-white px-6 py-2 rounded hover:bg-purple-700 text-sm disabled:opacity-50">
            {save.isPending ? 'Saving...' : 'Save Team'}
          </button>
          <button onClick={() => navigate('/')}
            className="border px-6 py-2 rounded hover:bg-gray-50 text-sm">
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Wire into `App.tsx`**

```typescript
import TeamBuilder from './pages/Builder/TeamBuilder'
// Replace <div>Team Builder coming soon</div> with <TeamBuilder />
```

- [ ] **Step 3: Verify in browser**

- [ ] **Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: no-code team builder with sequential, orchestrator, and loop modes"
```

---

### Task 15: Playground — chat interface

**Files:**
- Create: `frontend/src/components/ChatWindow.tsx`
- Create: `frontend/src/components/StepTrace.tsx`
- Create: `frontend/src/components/FileUpload.tsx`
- Create: `frontend/src/pages/Playground/index.tsx`

- [ ] **Step 1: Create `frontend/src/components/StepTrace.tsx`**

```typescript
import { useState } from 'react'

interface Step { step: number; agent_name: string; output?: string }

export default function StepTrace({ steps }: { steps: Step[] }) {
  const [open, setOpen] = useState<number | null>(null)
  if (steps.length === 0) return null
  return (
    <div className="text-xs text-gray-500 mt-2 space-y-1">
      {steps.map(s => (
        <div key={s.step} className="border rounded p-2">
          <button className="flex items-center gap-1 w-full text-left"
            onClick={() => setOpen(open === s.step ? null : s.step)}>
            <span className={`${open === s.step ? '▼' : '▶'}`} />
            <span>Step {s.step}: {s.agent_name}</span>
          </button>
          {open === s.step && s.output && (
            <pre className="mt-2 text-xs bg-gray-50 p-2 rounded whitespace-pre-wrap">{s.output}</pre>
          )}
        </div>
      ))}
    </div>
  )
}
```

- [ ] **Step 2: Create `frontend/src/components/ChatWindow.tsx`**

```typescript
import { useState, useRef, useEffect } from 'react'
import StepTrace from './StepTrace'

interface Message { role: string; text: string; steps?: any[] }

interface ChatWindowProps {
  conversationId: string
  onSend: (message: string, attachmentIds: string[]) => AsyncGenerator<any, void, unknown>
  onUpload: (file: File) => Promise<{ attachment_id: string; filename: string }>
}

export default function ChatWindow({ conversationId, onSend, onUpload }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [pendingAttachments, setPendingAttachments] = useState<{ id: string; name: string }[]>([])
  const [streaming, setStreaming] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const handleSend = async () => {
    if (!input.trim() || streaming) return
    const userMsg = input.trim()
    const attachIds = pendingAttachments.map(a => a.id)
    setInput('')
    setPendingAttachments([])
    setMessages(m => [...m, { role: 'user', text: userMsg }])
    setStreaming(true)

    let assistantText = ''
    let steps: any[] = []
    let currentStep: any = null

    setMessages(m => [...m, { role: 'assistant', text: '', steps: [] }])

    try {
      const gen = onSend(userMsg, attachIds)
      for await (const event of gen) {
        if (event.event === 'token') {
          assistantText += event.data.text
          setMessages(m => {
            const copy = [...m]
            copy[copy.length - 1] = { role: 'assistant', text: assistantText, steps }
            return copy
          })
        } else if (event.event === 'step_start') {
          currentStep = { step: event.data.step, agent_name: event.data.agent_name, output: '' }
        } else if (event.event === 'step_end' && currentStep) {
          steps = [...steps, currentStep]
          currentStep = null
          setMessages(m => {
            const copy = [...m]
            copy[copy.length - 1] = { role: 'assistant', text: assistantText, steps }
            return copy
          })
        }
      }
    } finally {
      setStreaming(false)
    }
  }

  const handleUpload = async (file: File) => {
    const result = await onUpload(file)
    setPendingAttachments(a => [...a, { id: result.attachment_id, name: result.filename }])
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
              m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-900'
            }`}>
              <p className="whitespace-pre-wrap">{m.text}</p>
              {m.steps && <StepTrace steps={m.steps} />}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {pendingAttachments.length > 0 && (
        <div className="px-4 py-2 flex flex-wrap gap-2">
          {pendingAttachments.map(a => (
            <span key={a.id} className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded flex items-center gap-1">
              📎 {a.name}
              <button onClick={() => setPendingAttachments(p => p.filter(x => x.id !== a.id))}
                className="text-blue-400 hover:text-blue-700">×</button>
            </span>
          ))}
        </div>
      )}

      <div className="border-t p-4 flex gap-2 items-end">
        <label className="cursor-pointer text-gray-400 hover:text-gray-600">
          <span className="text-xl">📎</span>
          <input type="file" className="hidden"
            accept=".pdf,.xlsx,.xls,.docx,.doc"
            onChange={e => e.target.files?.[0] && handleUpload(e.target.files[0])} />
        </label>
        <textarea
          className="flex-1 border rounded px-3 py-2 text-sm resize-none"
          rows={2}
          placeholder="Type a message..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
        />
        <button onClick={handleSend} disabled={streaming || !input.trim()}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm disabled:opacity-50">
          {streaming ? '...' : 'Send'}
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Create `frontend/src/pages/Playground/index.tsx`**

```typescript
import { useParams, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import ChatWindow from '../../components/ChatWindow'
import { createConversation, uploadFile } from '../../api/conversations'
import client from '../../api/client'

export default function Playground() {
  const { type, id } = useParams<{ type: string; id: string }>()
  const navigate = useNavigate()
  const [convId, setConvId] = useState<string | null>(null)
  const [targetName, setTargetName] = useState('')

  useEffect(() => {
    // Load target name
    if (type && id) {
      const url = type === 'agent' ? `/api/agents/${id}` : `/api/teams/${id}`
      client.get(url).then(r => setTargetName(r.data.name))
    }
    // Create or resume conversation
    if (type && id) {
      createConversation({ title: `Chat with ${id}`, target_type: type, target_id: id })
        .then(conv => setConvId(conv.id))
    }
  }, [type, id])

  async function* handleSend(message: string, attachmentIds: string[]) {
    if (!convId) return
    const response = await fetch(`/api/conversations/${convId}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CCM-User': localStorage.getItem('ccm_user') || 'dev-user',
      },
      body: JSON.stringify({ message, attachment_ids: attachmentIds }),
    })
    if (!response.body) return
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      let event = ''
      for (const line of lines) {
        if (line.startsWith('event: ')) event = line.slice(7)
        if (line.startsWith('data: ')) {
          try { yield { event, data: JSON.parse(line.slice(6)) } } catch {}
        }
      }
    }
  }

  const handleUpload = async (file: File) => {
    if (!convId) throw new Error('No conversation')
    return uploadFile(convId, file)
  }

  if (!convId) return <div className="flex items-center justify-center h-screen text-gray-400">Loading...</div>

  return (
    <div className="flex flex-col h-screen">
      <div className="border-b px-4 py-3 flex items-center gap-3">
        <button onClick={() => navigate('/')} className="text-gray-400 hover:text-gray-600">←</button>
        <span className="text-sm font-medium text-gray-900">{targetName || id}</span>
        <span className="text-xs text-gray-400 capitalize">{type}</span>
      </div>
      <div className="flex-1 overflow-hidden">
        {convId && <ChatWindow conversationId={convId} onSend={handleSend} onUpload={handleUpload} />}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Wire into `App.tsx`**

```typescript
import Playground from './pages/Playground'
// Replace <div>Playground coming soon</div> with <Playground />
```

- [ ] **Step 5: Verify full flow in browser**

1. Hub loads at `/`
2. Create an agent at `/builder/agent`
3. Hub shows agent card with "Use in Playground"
4. Playground opens at `/playground/agent/<id>`
5. Send a message — SSE streams tokens into chat

- [ ] **Step 6: Commit**

```bash
git add frontend/src/
git commit -m "feat: playground with SSE streaming chat, file upload, and step trace"
```

---

### Task 16: docker-compose and final wiring

**Files:**
- Create: `docker-compose.yml`
- Create: `backend/models/__init__.py`

- [ ] **Step 1: Create `docker-compose.yml`**

```yaml
version: '3.9'
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
      - ./ccm_hub.db:/app/ccm_hub.db
    env_file:
      - .env
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    depends_on:
      - backend
```

- [ ] **Step 2: Create `backend/Dockerfile`**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --pre -r requirements.txt
COPY . .
```

- [ ] **Step 3: Create `frontend/Dockerfile`**

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json .
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]
```

- [ ] **Step 4: Run full test suite**

```bash
cd backend && pytest ../tests/ -v
```
Expected: all tests pass.

- [ ] **Step 5: Final commit**

```bash
git add docker-compose.yml backend/Dockerfile frontend/Dockerfile
git commit -m "feat: docker-compose for backend + frontend"
```

---

## Summary

| Phase | Tasks | Deliverable |
|---|---|---|
| 1: Foundation | 1-2 | Backend + frontend scaffolded, health check passing |
| 2: Models | 3-4 | All DB models, auth middleware |
| 3: APIs | 5-8 | All CRUD + file upload endpoints |
| 4: Execution | 9-11 | Skill runner, agent SSE, all team modes |
| 5: Frontend | 12-16 | Hub, Builder, Playground, Docker |

Run all backend tests at any point with:
```bash
cd backend && pytest ../tests/ -v
```
