import pytest
from sqlalchemy import select
from backend.models.user import User
from backend.models.agent import Agent
from backend.models.marketplace import MarketplaceItem


@pytest.mark.asyncio
async def test_create_user(db):
    user = User(username="bob_model", display_name="Bob Model")
    db.add(user)
    await db.commit()
    result = await db.execute(select(User).where(User.username == "bob_model"))
    assert result.scalar_one().display_name == "Bob Model"


@pytest.mark.asyncio
async def test_create_agent(db):
    user = User(username="bob_agent", display_name="Bob Agent")
    db.add(user)
    await db.commit()
    agent = Agent(
        name="Credit Bot",
        description="desc",
        system_prompt="You are...",
        model="gpt-4.1",
        created_by=user.id,
    )
    db.add(agent)
    await db.commit()
    result = await db.execute(select(Agent).where(Agent.name == "Credit Bot"))
    assert result.scalar_one() is not None
