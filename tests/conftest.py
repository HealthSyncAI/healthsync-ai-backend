
from app.db.database import engine, Base
from sqlalchemy import text
import pytest_asyncio

import app.models.user
import app.models.health_record
import app.models.chat_session
import app.models.appointment


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(Base.metadata.create_all)
    yield