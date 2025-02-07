import asyncio

from app.db.database import engine, Base

# Import all model modules so that they are registered in Base.metadata
import app.models.user  # noqa
import app.models.chat_session  # noqa
import app.models.appointment  # noqa
import app.models.health_record  # noqa


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(create_tables())
    print("Tables created successfully.")
