import pytest
from datetime import datetime
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.db.database import get_db_session
from app.services.auth import get_current_user


class DummyUser:
    id = 1
    username = "dummy_user"


async def dummy_get_current_user():
    """Return a dummy user to bypass real authentication."""
    return DummyUser()


class DummyChatSessionObj:
    """A dummy chat session object to simulate a DB record."""

    def __init__(self, id, input_text, model_response, triage_advice, created_at):
        self.id = id
        self.input_text = input_text
        self.model_response = model_response  # will be mapped to the Pydantic "analysis" field
        self.triage_advice = triage_advice
        self.created_at = created_at


class DummyResult:
    """A dummy result to simulate SQLAlchemy query result."""

    def __init__(self, items):
        self._items = items

    def scalars(self):
        return self

    def all(self):
        return self._items


class DummyDBSessionForChats:
    """A dummy DB session for the GET /chats endpoint simulation."""

    async def execute(self, query):
        # Create two dummy chat sessions with different created_at values.
        dummy_session1 = DummyChatSessionObj(
            1,
            "I feel dizzy",
            "Possible dehydration",
            "Hydrate well and rest",
            datetime(2025, 2, 8, 12, 0, 0),
        )
        dummy_session2 = DummyChatSessionObj(
            2,
            "I have a fever",
            "Could be a viral infection",
            None,
            datetime(2025, 2, 7, 11, 0, 0),
        )
        # The endpoint orders by created_at descending, so dummy_session1 should appear first.
        return DummyResult([dummy_session1, dummy_session2])


async def dummy_get_db_session():
    """Yield a dummy DB session for GET /chats."""
    yield DummyDBSessionForChats()


@pytest.mark.asyncio
async def test_get_user_chats():
    """
    Test the /chats endpoint:
    - Override authentication and DB dependencies with dummy objects.
    - Send a GET request and verify the response contains the expected dummy chat sessions.
    """
    app.dependency_overrides[get_current_user] = dummy_get_current_user
    app.dependency_overrides[get_db_session] = dummy_get_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        response = await async_client.get("api/chatbot/chats")
        assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
        data = response.json()
        # Data should be a list of chat sessions with the fields id, input_text, analysis, triage_advice, created_at.
        assert isinstance(data, list), "Response is not a list."
        # Expecting two dummy chat sessions.
        assert len(data) == 2

        # Validate the first (most recent) chat session.
        chat1 = data[0]
        assert chat1["id"] == 1, "First chat session ID does not match expected value."
        assert chat1["input_text"] == "I feel dizzy", "First chat session input text mismatch."
        assert chat1["model_response"] == "Possible dehydration", "First chat session analysis mismatch."
        assert chat1["triage_advice"] == "Hydrate well and rest", "First chat session triage_advice mismatch."

        # Validate the second chat session.
        chat2 = data[1]
        assert chat2["id"] == 2, "Second chat session ID does not match expected value."
        assert chat2["input_text"] == "I have a fever", "Second chat session input text mismatch."
        assert chat2["model_response"] == "Could be a viral infection", "Second chat session analysis mismatch."
        assert chat2["triage_advice"] is None, "Second chat session triage_advice should be None."

        print("Test GET /chats passed with response:", data)

    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db_session, None)
