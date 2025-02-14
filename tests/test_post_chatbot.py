import pytest
from httpx import AsyncClient, ASGITransport

from app.db.database import get_db_session
from app.main import app
from app.services.auth import get_current_user


class DummyUser:
    id = 1
    username = "dummy_user"


async def dummy_get_current_user():
    """Return a dummy user to bypass real authentication."""
    return DummyUser()


class DummySession:
    def add(self, instance):
        pass

    async def commit(self):
        pass

    async def refresh(self, instance):
        instance.id = 1


async def dummy_get_db_session():
    """Yield a dummy session instead of a real DB session."""
    yield DummySession()


class DummyMessage:
    def __init__(self, content):
        self.content = content


class DummyChoice:
    def __init__(self, content):
        self.message = DummyMessage(content)


class DummyResponse:
    def __init__(self, content):
        self.choices = [DummyChoice(content)]


def dummy_completion_create(*args, **kwargs):
    """
    Simulate a call to the OpenAI completion endpoint.
    Returns a dummy response with a fixed analysis text.
    """
    return DummyResponse("Dummy analysis: Likely migraine. Suggest rest and hydration.")


@pytest.mark.asyncio
async def test_analyze_symptoms(monkeypatch):
    """
    Test the /symptom endpoint:
    - Override authentication and DB dependencies with dummy objects.
    - Monkey-patch the OpenAI client's chat.completions.create method.
    - Send a POST request and verify the response.
    """
    app.dependency_overrides[get_current_user] = dummy_get_current_user
    app.dependency_overrides[get_db_session] = dummy_get_db_session

    from app.ai.chatbot import client

    monkeypatch.setattr(client.chat.completions, "create", dummy_completion_create)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        payload = {"symptom_text": "I have a bad headache and sensitivity to light."}
        response = await async_client.post("api/chatbot/symptom", json=payload)

        assert response.status_code == 200, f"Unexpected response: {response.text}"
        data = response.json()
        assert data["input_text"] == payload["symptom_text"]
        assert "Dummy analysis" in data["analysis"]
        assert data.get("triage_advice") is None
        assert data.get("model_response") is None

        print("Test /symptom passed with response:", data)

    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db_session, None)
