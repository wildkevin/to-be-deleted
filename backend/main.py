from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import engine, Base

# Import all models so tables are created
from backend.models import user, agent, team, marketplace, conversation  # noqa

from backend.api import agents, teams, marketplace as marketplace_api, conversations

app = FastAPI(title="CCM Agent Hub")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router)
app.include_router(teams.router)
app.include_router(marketplace_api.router)
app.include_router(conversations.router)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health():
    return {"status": "ok"}
