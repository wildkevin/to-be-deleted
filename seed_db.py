#!/usr/bin/env python3
"""
Seed the database with initial users.
Run this once before starting the application.
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from backend.models.user import User
from backend.database import Base
import os

DB_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ccm_hub.db")


async def seed_users():
    engine = create_async_engine(DB_URL)
    
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        # Check if users already exist
        from sqlalchemy import select
        result = await session.execute(select(User))
        existing_users = result.scalars().all()
        
        if existing_users:
            print(f"Database already has {len(existing_users)} user(s). Skipping seed.")
            for user in existing_users:
                print(f"  - {user.username} ({'admin' if user.is_admin else 'user'})")
            return
        
        # Seed initial users
        session.add_all([
            User(username="alice", display_name="Alice", is_admin=False),
            User(username="admin", display_name="Admin", is_admin=True),
        ])
        await session.commit()
        print("Seeded database with initial users:")
        print("  - alice (user)")
        print("  - admin (admin)")


if __name__ == "__main__":
    asyncio.run(seed_users())
