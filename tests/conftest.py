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
        session.add_all(
            [
                User(username="alice", display_name="Alice", is_admin=False),
                User(username="admin", display_name="Admin", is_admin=True),
            ]
        )
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
