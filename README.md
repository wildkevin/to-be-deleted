# CCM Agent Hub

An internal web app for Credit Capital Management analysts to create, share, and interact with AI agents and agent teams powered by Azure OpenAI.

## Tech Stack

**Backend**
- Python 3.11+
- FastAPI
- SQLAlchemy (async) + aiosqlite
- agent-framework for agent execution
- Azure OpenAI integration

**Frontend**
- React 18
- TypeScript
- Vite
- TailwindCSS
- React Query
- React Router

## Prerequisites

1. **Python 3.11+**
2. **Node.js** (for frontend)

## Setup

### 1. Backend Setup

```bash
# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your Azure OpenAI credentials
```

### 2. Seed Database

```bash
# From project root
python seed_db.py
```

This creates two users:
- `alice` (regular user)
- `admin` (admin user)

### 3. Frontend Setup

```bash
cd frontend
npm install
```

## Running the Application

### Start Backend

```bash
# From project root
source .venv/bin/activate
uvicorn backend.main:app --reload
```

Backend will be available at `http://localhost:8000`

### Start Frontend

In a new terminal:

```bash
cd frontend
npm run dev
```

Frontend will be available at `http://localhost:5173`

## Testing

```bash
# Run backend tests
pytest tests/ -v
```

All 24 tests should pass.

## Features

### Hub Page
- Browse all agents, teams, MCP tools, and skills
- Create new agents and teams

### Agent Builder
- Configure agent name, description, and model
- Set system prompt
- Attach MCP tools and skills from marketplace

### Team Builder
- Select collaboration mode (sequential, orchestrator, loop)
- Add agents to team
- Configure orchestrator (for orchestrator mode)
- Set max iterations and stop signal (for loop mode)

### Playground
- Interactive chat interface with SSE streaming
- Step-by-step agent execution tracing
- File upload support for document analysis

## API Endpoints

### Agents
- `GET /api/agents` - List agents
- `POST /api/agents` - Create agent
- `GET /api/agents/{id}` - Get agent details
- `PUT /api/agents/{id}` - Update agent
- `DELETE /api/agents/{id}` - Delete agent

### Teams
- `GET /api/teams` - List teams
- `POST /api/teams` - Create team
- `DELETE /api/teams/{id}` - Delete team

### Conversations
- `GET /api/conversations` - List conversations
- `POST /api/conversations` - Create conversation
- `GET /api/conversations/{id}/chat` - Stream chat (SSE)
- `POST /api/conversations/{id}/upload` - Upload file

### Marketplace
- `GET /api/marketplace` - List approved items
- `POST /api/marketplace/mcp` - Submit MCP tool
- `POST /api/marketplace/skill` - Submit skill
- `POST /api/marketplace/{id}/approve` - Approve item (admin only)
- `POST /api/marketplace/{id}/reject` - Reject item (admin only)

## Authentication

The app uses header-based authentication:
- Header: `X-CCM-User`
- Valid users: `alice`, `admin`
- Admin users can approve/reject marketplace items

## License

Internal use only.
