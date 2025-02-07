import pytest_asyncio
from sqlalchemy import text, select
from app.db.database import engine, Base, AsyncSessionLocal

# Import all model modules so that they are registered in Base.metadata
import app.models.user  # noqa
import app.models.chat_session  # noqa
import app.models.appointment  # noqa
import app.models.health_record  # noqa


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(Base.metadata.create_all)
