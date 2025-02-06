import uuid
import pytest_asyncio
from sqlalchemy import text
from app.db.database import engine, Base, AsyncSessionLocal
from app.models.user import User as UserModel

# Ensure that all models are imported, so Base.metadata is complete.
import app.models.user
import app.models.health_record
import app.models.chat_session
import app.models.appointment

@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """
    Reset the public schema before each test for a clean database state.
    """
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Optionally, add teardown code here.

@pytest_asyncio.fixture
async def dummy_user():
    """
    Create and return a dummy user with a unique username for each test.
    """
    unique_username = f"testuser_{uuid.uuid4()}"  # Generate a unique username
    async with AsyncSessionLocal() as session:  # Use AsyncSessionLocal directly.
        user = UserModel(
            username=unique_username,
            email=f"{unique_username}@example.com",
            hashed_password="dummy",  # For test purposes only.
            role="patient"
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

@pytest_asyncio.fixture(autouse=True)
def override_get_current_user(dummy_user):
    """
    Override the get_current_user dependency to always return the dummy user.
    This ensures that authentication-dependent endpoints use the dummy user during tests.
    """
    from app.main import app
    from app.services.auth import get_current_user

    # The dependency override will return the dummy user created by the fixture.
    app.dependency_overrides[get_current_user] = lambda: dummy_user  # type: ignore
    yield
    app.dependency_overrides.pop(get_current_user, None)  # type: ignore
