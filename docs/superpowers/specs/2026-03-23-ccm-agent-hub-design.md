# CCM Agent Hub — Design Spec

**Date:** 2026-03-23
**Department:** Credit Capital Management (CCM)
**Status:** Draft

---

## 1. Overview

The CCM Agent Hub is an internal web application that enables analysts and bankers in the Credit Capital Management department to build, share, and interact with AI agents and agent teams. It supports the full credit lending user journey — credit memo generation, financial analysis, unstructured data transformation, company background generation, capital optimization, and more.

All CCM users have equal access. Agents and teams built by any user become available to the entire CCM group.

---

## 2. Concepts

### Agent
A configured AI assistant: a name, a system prompt, a model selection, and a set of MCP tools and/or skills it can call. Built via the no-code builder.

### Team
A group of agents that collaborate to handle a user request. Collaboration mode is user-defined: sequential, orchestrator, or loop.

### MCP Tool
An external tool exposed via the Model Context Protocol (MCP). Users register an MCP server by providing its URL and auth headers; the portal auto-discovers all available tools from the server via `MCPStreamableHTTPTool` (no manual schema entry). At runtime, `agent-framework` connects to the MCP server and exposes its tools to the agent as callable functions.

### Skill
A pre-packaged, reusable capability registered in the marketplace. A skill is a Python callable (a function) with a defined input/output schema, exposed to the LLM as a callable function the same way MCP tools are. Skills are authored in Python, uploaded as a `.py` file during marketplace submission, and executed in a sandboxed subprocess at runtime by `skill_runner`. Examples: "Extract financial ratios from a document", "Format output as a credit memo".

---

## 3. Architecture

**Approach:** Monorepo, single FastAPI backend + React SPA frontend.

**Agent Framework:** `agent-framework==1.0.0rc4` (Microsoft) — handles agent execution, MCP tool integration via `MCPStreamableHTTPTool`, and multi-agent orchestration patterns.

```
ccm-ai-agentic-suite/
├── backend/                  # FastAPI app
│   ├── api/                  # Route handlers
│   │   ├── agents.py
│   │   ├── teams.py
│   │   ├── marketplace.py
│   │   ├── playground.py
│   │   └── conversations.py
│   ├── core/                 # Business logic
│   │   ├── agent_runner.py   # Single agent execution via agent-framework ChatAgent
│   │   ├── team_runner.py    # Team execution (sequential/orchestrator/loop)
│   │   └── skill_runner.py   # Skill subprocess execution
│   ├── storage/              # Storage abstraction
│   │   ├── base.py           # StorageClient interface
│   │   └── local.py          # Local disk implementation (future: azure_blob.py)
│   ├── models/               # SQLAlchemy DB models
│   ├── schemas/              # Pydantic schemas
│   └── main.py
├── frontend/                 # React SPA (Vite + TypeScript)
│   ├── pages/
│   │   ├── Hub/              # Browse agents, teams, MCPs, skills
│   │   ├── Builder/          # No-code agent & team builder
│   │   └── Playground/       # Chat interface
│   └── components/
└── docker-compose.yml        # Runs backend (port 8000) + frontend (port 5173)
```

**LLM Provider:** Azure OpenAI (gpt-4.1-mini, gpt-4.1, gpt-5, gpt-5.1)

**Data Store:**
- Now: SQLite (via SQLAlchemy)
- Future: Azure PostgreSQL — swap `DATABASE_URL` env var; no schema changes needed

**File Storage:**
- Now: Local disk (path configured via `STORAGE_PATH` env var)
- Future: Azure Blob Storage — implement `StorageClient` interface in `storage/azure_blob.py`

**Streaming:** FastAPI Server-Sent Events (SSE) for real-time chat responses.

---

## 4. Pages & Features

### Hub (Marketplace)
- Tabbed/filtered browse grid: Agents, Teams, MCPs, Skills
- Each card: name, description, creator, tags, "Use in Playground" CTA
- MCPs and Skills show status badge: `approved` / `pending review`
- Any user can submit a new MCP or skill (enters admin review queue)

### No-Code Agent Builder
Form-based configuration:
- **Name** — display name
- **Description** — purpose summary
- **System Prompt** — rich text instruction for the agent
- **Model** — dropdown: gpt-4.1-mini | gpt-4.1 | gpt-5 | gpt-5.1
- **MCP Tools** — multi-select from `GET /api/marketplace?type=mcp` (approved only)
- **Skills** — multi-select from `GET /api/marketplace?type=skill` (approved only)
- Save → agent published to Hub, visible to all CCM

### No-Code Team Builder
- Select agents from the Hub to form the team
- Pick collaboration mode:
  - **Sequential** — define agent execution order (drag to reorder)
  - **Orchestrator** — designate one lead agent from the team that routes to the others
  - **Loop** — all agents in the team run sequentially within each iteration, cycling until a stop condition is met
- Save → team published to Hub, visible to all CCM

### Playground
- Chat interface with SSE streaming
- File upload (PDF, Excel, Word). Uploaded files return an `attachment_id`; the user attaches it to the next chat message by including `attachment_ids` in the chat request.
- Conversation history persisted and resumable across sessions
- Supports both single agents and teams
- Intermediate agent steps visible (collapsible) for team runs

---

## 5. Data Models

```
User
  id, username, display_name
  is_admin: bool  -- grants access to marketplace moderation endpoints
  created_at
  Note: In phase 1, users are identified by the X-CCM-User header
  (username string). If the header is absent, the server returns 401.
  No authentication middleware beyond header presence + user lookup.
  Admin users seeded manually in the DB.

Agent
  id: UUID, name, description, system_prompt
  model: enum(gpt-4.1-mini | gpt-4.1 | gpt-5 | gpt-5.1)
  mcp_tools: [MarketplaceItem]   -- many-to-many join
  skills: [MarketplaceItem]      -- many-to-many join
  created_by (-> User.id), created_at, updated_at

Team
  id: UUID, name, description
  mode: enum(sequential | orchestrator | loop)
  agents: ordered via TeamAgent join table (see below)
  orchestrator_agent_id -> Agent.id (nullable; must be an agent already in this team's agents list)
  loop_max_iterations: int (nullable; default 5 for loop mode)
  loop_stop_signal: str (nullable; if null, loop always runs to loop_max_iterations;
                         if set, loop also stops early when this keyword is found in any
                         iteration's output, case-insensitive substring match)
  created_by (-> User.id), created_at, updated_at

TeamAgent (join table)
  team_id, agent_id, position: int  -- position determines sequential order and loop order

MarketplaceItem
  id: UUID, name, description
  type: enum(mcp | skill)
  config: JSON
    -- for mcp:   { "server_url": str, "auth_headers": { "Authorization": "Bearer ..." } }
                  Tool schemas are NOT stored — auto-discovered at runtime via MCPStreamableHTTPTool.
    -- for skill: { "function_name": str, "input_schema": {...}, "output_schema": {...} }
  file_path: str (nullable; for skill type only — path to uploaded .py file)
  status: enum(pending | approved | rejected)
  submitted_by (-> User.id)
  reviewed_by (-> User.id, nullable)
  status_changed_at: datetime (nullable)
  created_at

Conversation
  id: UUID, title
  target_type: enum(agent | team)
  target_id: UUID  -- references Agent.id or Team.id (polymorphic; no DB-level FK)
  created_by (-> User.id), created_at

Message
  id: UUID, conversation_id (-> Conversation.id)
  role: enum(user | assistant | tool)
  content: JSON
    -- user:      { "text": "..." }
    -- assistant: { "text": "...", "agent_name": "..." }
                  (agent_name identifies which agent produced this response;
                   for team runs, only the final agent's response is stored
                   as role=assistant; intermediate agents' outputs are stored
                   as role=tool messages for replay purposes)
    -- tool:      { "tool_call_id": "...", "tool_name": "...", "result": {...} }
  created_at

Attachment
  id: UUID, message_id (-> Message.id, nullable — set after the chat message is created)
  conversation_id (-> Conversation.id)  -- set at upload time for pre-attachment
  filename, file_path, mime_type, size: int
  extracted_text: text  -- pre-extracted at upload time; injected into context
  created_at
```

**Deletion rules:**
- `DELETE /api/agents/{id}`: blocked (returns `409 Conflict`) if the agent is a member of any team. User must remove it from teams first.
- `DELETE /api/teams/{id}`: cascades to `TeamAgent` rows. Does not delete constituent agents.
- `DELETE /api/conversations/{id}`: cascades to `Message` and `Attachment` rows; also deletes stored files from disk.

---

## 6. API Design

All list endpoints support `?page=1&limit=20` query params. Responses use the envelope:
```json
{ "items": [...], "total": 0, "page": 1, "limit": 20 }
```

```
# Agents
GET    /api/agents                    -- list all agents (paginated)
POST   /api/agents                    -- create agent
GET    /api/agents/{id}               -- get agent
PUT    /api/agents/{id}               -- full replace (all fields required)
DELETE /api/agents/{id}               -- blocked if agent is in any team (409)

# Teams
GET    /api/teams                     -- list all teams (paginated)
POST   /api/teams                     -- create team
GET    /api/teams/{id}                -- get team
PUT    /api/teams/{id}                -- full replace (all fields required)
DELETE /api/teams/{id}                -- cascades to TeamAgent rows

# Marketplace
GET    /api/marketplace               -- list approved items; supports ?type=mcp|skill
POST   /api/marketplace/submit        -- submit new MCP or skill (multipart/form-data)
GET    /api/marketplace/pending       -- admin only: list pending submissions
POST   /api/marketplace/{id}/approve  -- admin only
POST   /api/marketplace/{id}/reject   -- admin only

# Conversations / Playground
GET    /api/conversations             -- list user's conversations (paginated)
POST   /api/conversations             -- create new conversation
GET    /api/conversations/{id}        -- get conversation + all messages
POST   /api/conversations/{id}/chat   -- send message (SSE streaming, see §7)
POST   /api/conversations/{id}/upload -- upload file (see §8)
DELETE /api/conversations/{id}        -- cascades to messages, attachments, files
```

**MCP submit request (multipart/form-data):**
```
name:         string
description:  string
type:         "mcp"
server_url:   string  -- the MCP server HTTP/SSE endpoint
auth_headers: JSON string  -- e.g. { "Authorization": "Bearer <token>" }
```
On submission, the backend attempts to connect via `MCPStreamableHTTPTool` to validate the server is reachable and discover its tools. If connection fails, submission is rejected with `400`. Discovered tool names are stored for display in the admin review UI.

**Skill submit request (multipart/form-data):**
```
name:          string
description:   string
type:          "skill"
function_name: string  -- name of the callable inside the uploaded file
input_schema:  JSON string  -- JSON Schema for function arguments
output_schema: JSON string  -- JSON Schema for return value
file:          the .py file containing the callable
```

---

## 7. SSE Streaming Contract

`POST /api/conversations/{id}/chat`

**Request body:**
```json
{
  "message": "Analyze the uploaded financial statement",
  "attachment_ids": ["uuid1", "uuid2"]  // optional; IDs from prior /upload calls
}
```

**Response:** `Content-Type: text/event-stream`

Event types:

```
event: step_start
data: { "step": 1, "agent_name": "Credit Analyst" }

event: token
data: { "text": "Based on the financials..." }

event: tool_call
data: { "tool_name": "get_company_profile", "args": {...} }

event: tool_result
data: { "tool_name": "get_company_profile", "result": {...} }

event: step_end
data: { "step": 1, "agent_name": "Credit Analyst" }

event: done
data: { "message_id": "uuid" }

event: error
data: { "code": "azure_error|skill_error|mcp_timeout|parse_error", "message": "..." }
```

**Token streaming rules by mode:**
- **Single agent:** one `step_start`/`step_end` pair. Tokens from the agent are streamed.
- **Sequential:** one `step_start`/`step_end` pair per agent. Only the final agent's tokens are streamed to the UI; intermediate agents' outputs are emitted only as `step_start`/`step_end` events (no tokens).
- **Orchestrator:** the lead agent's tokens are streamed (including its reasoning between specialist calls). Specialist agents run and return buffered results to the lead. Each specialist invocation emits a `step_start`/`step_end` pair.
- **Loop:** each iteration emits a `step_start`/`step_end` pair (with iteration number in `step`). Only the final iteration's tokens are streamed.

The stream closes after `done` or `error`.

---

## 8. File Upload Contract

`POST /api/conversations/{id}/upload`
- **Request:** `multipart/form-data` with field `file`
- **Accepted types:** PDF, XLSX, XLS, DOCX, DOC
- **Size limit:** 20 MB per file
- **Processing:** Text extracted synchronously at upload time (PDF→text, Excel→markdown table, Word→text). File stored to `{STORAGE_PATH}/{conversation_id}/{uuid}_{filename}`.
- **Response:**
  ```json
  {
    "attachment_id": "uuid",
    "filename": "report.pdf",
    "mime_type": "application/pdf",
    "size": 204800,
    "extracted_text_preview": "First 500 chars..."
  }
  ```
- The returned `attachment_id` is passed in `attachment_ids` of the subsequent chat request. The extracted text of all referenced attachments is injected into the context window before the user's message.
- If text extraction fails, returns `400 { "error": "Could not extract text from file" }` and the file is not stored.

---

## 9. Agent & Team Execution

### Context Window
- History: last `CONTEXT_WINDOW_MESSAGES` messages (default: 20, configurable via env var).
- Attached file text is prepended to the user's message turn, clearly delimited: `--- File: {filename} ---\n{extracted_text}\n---`.
- No automatic token-budget truncation in phase 1; the 20-message default is conservative enough for most credit workflows.

### Skill Execution
`skill_runner` loads and executes user-submitted Python callables in an isolated subprocess (via Python `subprocess` module with a 30-second timeout). The subprocess receives the function arguments as JSON on stdin and returns the result as JSON on stdout. This prevents user-submitted code from affecting the main process. The subprocess runs with no network access and read-only filesystem access to the skill's `.py` file.

### Single Agent
1. User sends message (with optional attachment_ids)
2. `agent_runner` builds context: system prompt + last N messages + extracted file text
3. Instantiates `agent_framework.ChatAgent` with the configured Azure OpenAI client and model
4. MCP tools: instantiated as `MCPStreamableHTTPTool(name, server_url, headers)` — tools auto-discovered from server
5. Skills: wrapped as `AIFunction` callables, dispatched via `skill_runner` subprocess
6. `ChatAgent.run()` handles the function-calling loop internally; `agent_runner` streams tokens via SSE as they arrive

### Team — Sequential
1. User message → Agent 1 runs to completion (output buffered)
2. Agent 1's full output becomes the user-side input to Agent 2 → ... → final agent
3. Final agent's response streamed as tokens; intermediate agents emit only `step_start`/`step_end`
4. Only the final agent's response is persisted as `role=assistant`; intermediate outputs stored as `role=tool` messages for conversation replay

### Team — Orchestrator
1. User message → Lead agent runs with function definitions for each specialist agent (function name = agent's `name`, description = agent's `description`, parameter = `{ "message": string }`)
2. When lead calls a specialist: specialist runs with the provided message string as its user input; result returned to lead as a tool result
3. Lead decides next specialist or responds directly
4. Lead's reasoning tokens (including between specialist calls) are streamed; specialist runs are buffered and emitted as `step_start`/`step_end` events

### Team — Loop
1. User message → all agents in the team run sequentially within each iteration (same as sequential mode for one pass)
2. After each iteration: check the final agent's output for `loop_stop_signal` keyword (if configured). If found, stop.
3. Also stops after `loop_max_iterations` (default: 5)
4. Only the final iteration's last agent response is streamed as tokens

### Error Handling
- **Azure OpenAI error:** emit `error` SSE event with `code: "azure_error"`. Do not retry. User re-sends.
- **MCP tool timeout (10s):** emit `tool_result` with `{ "error": "timeout" }` so the LLM can acknowledge and continue.
- **Skill execution failure (exception or timeout at 30s):** emit `tool_result` with `{ "error": "skill_error", "message": "..." }` so the LLM can acknowledge and continue. Also emit SSE `error` event with `code: "skill_error"`.
- **File parse failure:** `400` from upload endpoint. File not stored.
- **Missing resource:** `404`.
- **Admin endpoint unauthorized:** `403`.
- **Missing X-CCM-User header or unknown user:** `401`.
- **Agent delete blocked by team membership:** `409`.

---

## 10. Environment Variables

```
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_API_VERSION=2025-03-01-preview
# Note: use a preview API version that supports gpt-5/gpt-5.1 when available;
# update this value as new model deployments require newer API versions.

# Database
DATABASE_URL=sqlite:///./ccm_hub.db
# Future: DATABASE_URL=postgresql+asyncpg://user:pass@host/db

# File Storage
STORAGE_PATH=./uploads
# Future: AZURE_BLOB_CONNECTION_STRING=...
#         AZURE_BLOB_CONTAINER=ccm-uploads

# App
CORS_ORIGINS=http://localhost:5173
CONTEXT_WINDOW_MESSAGES=20
```

---

## 11. docker-compose

`docker-compose.yml` runs two services:
- **backend** — FastAPI on port 8000, mounts `./uploads` volume and `./ccm_hub.db`, reads `.env`
- **frontend** — Vite dev server on port 5173, proxies `/api` to `http://backend:8000`

No sidecar services required for phase 1 (SQLite is file-based).

---

## 12. Authorization

Flat access model — all CCM users have full access to agents, teams, marketplace browsing, and playground. Users identified by `X-CCM-User` request header (username string). If the header is absent or the username is unknown, the server returns `401`.

Admin functions (marketplace moderation) require `User.is_admin = true`. If `is_admin` is false, admin endpoints return `403`. Admin users seeded manually in the DB in phase 1.

---

## 13. Future Considerations

- **Azure PostgreSQL** — swap `DATABASE_URL`; SQLAlchemy abstracts the difference
- **Azure Blob Storage** — implement `StorageClient` interface in `storage/azure_blob.py`
- **Azure AD / SSO** — replace `X-CCM-User` header with proper JWT authentication
- **Agent versioning** — track changes to agents over time
- **Usage analytics** — which agents/teams are most used
- **Skill sandboxing hardening** — move skill execution to a dedicated container or Azure Function for stronger isolation
