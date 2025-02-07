import pytest_asyncio
from sqlalchemy import text

from app.db.database import test_engine, Base, get_db_session, get_test_db_session
import app

# Check that the test database URL contains "test"
db_url = str(test_engine.url)
if "test" not in db_url.lower():
    raise Exception(
        "The tests are configured to run on a test database. "
        f"Current test database URL: {db_url} does not appear to be a test DB!"
    )

# Import all model modules so they get registered in Base.metadata
import app.models.user  # noqa
import app.models.chat_session  # noqa
import app.models.appointment  # noqa
import app.models.health_record  # noqa


@pytest_asyncio.fixture(autouse=True, scope="session")
def override_db_dependency():
    """
    Temporarily override the production DB dependency (get_db_session)
    with the test DB dependency (get_test_db_session) for the test session.
    After tests finish, revert to the original dependency.
    """
    # Save any existing override for get_db_session
    original = app.app.dependency_overrides.get(get_db_session)
    # Set the override to use the test DB session dependency
    app.app.dependency_overrides[get_db_session] = get_test_db_session
    yield
    # Cleanup: restore the original dependency (or remove override if none)
    if original is not None:
        app.app.dependency_overrides[get_db_session] = original
    else:
        app.app.dependency_overrides.pop(get_db_session, None)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """
    Before each test, drop and recreate the schema in the test database.
    """
    async with test_engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(Base.metadata.create_all)
    yield