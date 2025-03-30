import pytest
from httpx import AsyncClient, ASGITransport
import json

from app.main import app
from app.db.database import get_db_session
from app.services.auth import AuthService
from app.ai import chatbot as chatbot_module


class DummyUser:
    id = 1
    username = "dummy_user"
    role = "patient"


async def dummy_get_current_user_method(*args, **kwargs):
    return DummyUser()


class DummyAuthService:
    async def get_current_user(self, token: str = None):
        return await dummy_get_current_user_method()


def dummy_auth_service_provider():
    return DummyAuthService()


class DummySession:
    _save_instance = None
    _room_number_counter = 0

    def add(self, instance):
        self._save_instance = instance
        if not hasattr(instance, "id") or instance.id is None:
            instance.id = 1

        if isinstance(instance, chatbot_module.ChatRoom):
            if instance.room_number is None:
                self._room_number_counter += 1
                instance.room_number = self._room_number_counter

    async def commit(self):
        pass

    async def refresh(self, instance):
        if not hasattr(instance, "id") or instance.id is None:
            instance.id = getattr(self._save_instance, "id", 1)

        if isinstance(instance, chatbot_module.ChatRoom) and hasattr(
            self._save_instance, "room_number"
        ):
            instance.room_number = self._save_instance.room_number

    async def execute(self, query):

        if "max(chat_rooms.room_number)" in str(query).lower():

            class MockScalarResultMax:
                def scalar(self):
                    return self._room_number_counter

            return MockScalarResultMax()

        elif (
            "chat_rooms.patient_id" in str(query).lower()
            and "chat_rooms.room_number" in str(query).lower()
        ):

            class MockScalarResultFind:

                def scalar_one_or_none(self):
                    return None

            return MockScalarResultFind()

        return type(
            "obj", (object,), {"scalar": lambda: 0, "scalar_one_or_none": lambda: None}
        )()


async def dummy_get_db_session():
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
        self._raw_response_str = f"DummyResponse(content='{content}')"

    def __str__(self):
        return self._raw_response_str


def dummy_completion_create(*args, **kwargs):
    return DummyResponse(
        "TRIAGE_SCHEDULE Based on your symptoms, it looks like a possible migraine. Suggest rest and hydration."
    )


@pytest.mark.asyncio
async def test_analyze_symptoms(monkeypatch):
    """
    Test the /symptom endpoint with corrected Auth (via override + dummy header),
    DB mocking, and OpenAI monkeypatching.
    """

    original_auth_override = app.dependency_overrides.get(AuthService)
    original_db_override = app.dependency_overrides.get(get_db_session)

    app.dependency_overrides[AuthService] = dummy_auth_service_provider
    app.dependency_overrides[get_db_session] = dummy_get_db_session

    monkeypatch.setattr(
        chatbot_module.client.chat.completions, "create", dummy_completion_create
    )

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as async_client:
            payload = {
                "symptom_text": "I have a bad headache and sensitivity to light."
            }

            headers = {"Authorization": "Bearer this_is_another_dummy_token"}

            response = await async_client.post(
                "api/chatbot/symptom", json=payload, headers=headers
            )

            assert (
                response.status_code == 200
            ), f"Unexpected status code: {response.status_code}, Response: {response.text}"
            data = response.json()
            assert data["input_text"] == payload["symptom_text"]
            assert "TRIAGE_SCHEDULE" in data["analysis"]
            assert "possible migraine" in data["analysis"]
            assert data["triage_advice"] == "schedule_appointment"
            assert data.get("model_response") is not None
            assert "DummyResponse" in data["model_response"]

            print("\nTest POST /symptom passed with response:")
            print(json.dumps(data, indent=2))

    finally:

        if original_auth_override:
            app.dependency_overrides[AuthService] = original_auth_override
        else:
            app.dependency_overrides.pop(AuthService, None)

        if original_db_override:
            app.dependency_overrides[get_db_session] = original_db_override
        else:
            app.dependency_overrides.pop(get_db_session, None)
