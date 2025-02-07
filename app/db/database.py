from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# --- Production Database Setup ---
engine = create_async_engine(settings.database_uri, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# --- Test Database Setup ---
test_engine = create_async_engine(settings.database_test_uri, echo=True)
TestAsyncSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

# Base for models (both engines will use the same metadata)
Base = declarative_base()


# Production DB session dependency
async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


# Test DB session dependency
async def get_test_db_session() -> AsyncSession:
    async with TestAsyncSessionLocal() as session:
        yield session
