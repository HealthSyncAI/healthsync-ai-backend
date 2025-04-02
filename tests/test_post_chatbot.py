import json

import pytest
from httpx import AsyncClient, ASGITransport

from app.ai import chatbot as chatbot_module
from app.db.database import get_db_session
from app.main import app
from app.models.chat_room import ChatRoom
from app.models.chat_session import ChatSession
from app.services.auth import AuthService


class DummyUser:
    id = 1
    username = "dummy_user"
    role = "patient"


async def dummy_get_current_user_method(*args, **kwargs):
    """Simulates retrieving the current user."""
    return DummyUser()


class DummyAuthService:
    async def get_current_user(self, token: str = None):
        """Mock method to get the dummy user."""
        return await dummy_get_current_user_method()


def dummy_auth_service_provider():
    """Provides the dummy auth service instance."""
    return DummyAuthService()


class DummySession:
    _save_instance = None
    _room_number_counter = 0

    def add(self, instance):
        """Simulates adding an object to the session."""
        self._save_instance = instance

        if not hasattr(instance, "id") or instance.id is None:
            instance.id = 1

        if isinstance(instance, ChatRoom):
            if not hasattr(instance, "room_number") or instance.room_number is None:
                self._room_number_counter += 1
                instance.room_number = self._room_number_counter
                print(
                    f"[Mock DB] Assigned room_number {instance.room_number} to new ChatRoom"
                )

    async def commit(self):
        """Simulates committing the transaction."""
        print("[Mock DB] Commit called")
        pass

    async def flush(self):
        """Simulates flushing the session. Important for getting IDs before commit."""
        print("[Mock DB] Flush called")

        if self._save_instance and (
            not hasattr(self._save_instance, "id") or self._save_instance.id is None
        ):
            self._save_instance.id = 1
            print(f"[Mock DB] Assigned ID {self._save_instance.id} on flush")
        pass

    async def refresh(self, instance):
        """Simulates refreshing the object state from the DB."""
        print(f"[Mock DB] Refresh called for instance: {instance}")

        if not hasattr(instance, "id") or instance.id is None:
            instance.id = getattr(self._save_instance, "id", 1)
            print(f"[Mock DB] Assigned ID {instance.id} on refresh")

        if isinstance(instance, ChatRoom) and hasattr(
            self._save_instance, "room_number"
        ):
            if instance.room_number != self._save_instance.room_number:
                print(
                    f"[Mock DB] Correcting room_number on refresh to {self._save_instance.room_number}"
                )
                instance.room_number = self._save_instance.room_number

        if isinstance(instance, ChatSession) and not hasattr(instance, "chat_room"):
            mock_room = ChatRoom(id=1, patient_id=instance.patient_id, room_number=1)
            instance.chat_room = mock_room
            print(f"[Mock DB] Added mock chat_room relationship on refresh")

    async def rollback(self):
        """Simulates rolling back the transaction."""

        print("[Mock DB] Rollback called")
        pass

    async def execute(self, query):
        """Simulates executing a query."""
        query_str = str(query).lower()
        print(f"[Mock DB] Execute called with query:\n{query_str}")

        if (
            "max(chat_rooms.room_number)" in query_str
            and "chat_rooms.patient_id" in query_str
        ):
            print(
                f"[Mock DB] Simulating max room number query, returning: {self._room_number_counter}"
            )

            class MockScalarResultMax:
                def scalar(self):
                    return DummySession._room_number_counter

            return MockScalarResultMax()

        elif (
            "chat_rooms.patient_id =" in query_str
            and "chat_rooms.room_number =" in query_str
        ):
            print("[Mock DB] Simulating find existing room query, returning: None")

            class MockScalarResultFind:
                def scalar_one_or_none(self):
                    return None

            return MockScalarResultFind()

        print("[Mock DB] Simulating generic query, returning default")

        class MockGenericResult:
            def scalar(self):
                return 0

            def scalar_one_or_none(self):
                return None

            def scalars(self):
                return self

            def all(self):
                return []

        return MockGenericResult()


async def dummy_get_db_session():
    """Dependency override for database session."""
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

        self._raw_response_str = json.dumps(
            {
                "id": "dummy-chatcmpl-123",
                "object": "chat.completion",
                "created": 1677652288,
                "model": "google/gemini-2.0-flash-exp:free",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": content,
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 9,
                    "completion_tokens": 12,
                    "total_tokens": 21,
                },
            }
        )

    def __str__(self):
        """Return the simulated raw JSON string representation."""
        return self._raw_response_str


def dummy_completion_create(*args, **kwargs):
    """Monkeypatch function for OpenAI client."""

    user_message = ""
    if "messages" in kwargs:
        for msg in kwargs["messages"]:
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
    print(f"[Mock OpenAI] Received user message: {user_message}")

    response_content = "TRIAGE_SCHEDULE Based on your symptoms of headache and light sensitivity, it could be a migraine. Please rest and stay hydrated. Consider scheduling an appointment if it persists."
    print(f"[Mock OpenAI] Returning dummy response content: {response_content}")
    return DummyResponse(response_content)


@pytest.mark.asyncio
async def test_analyze_symptoms(monkeypatch):
    """
    Test the /symptom endpoint with corrected Auth, DB mocking (including rollback),
    and OpenAI monkeypatching.
    """
    print("\n--- Starting test_analyze_symptoms ---")

    original_auth_override = app.dependency_overrides.get(AuthService)
    original_db_override = app.dependency_overrides.get(get_db_session)

    app.dependency_overrides[AuthService] = dummy_auth_service_provider
    app.dependency_overrides[get_db_session] = dummy_get_db_session
    print("[Setup] Applied mock DB and Auth overrides.")

    monkeypatch.setattr(
        chatbot_module.client.chat.completions, "create", dummy_completion_create
    )
    print("[Setup] Monkeypatched OpenAI client.")

    try:

        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as async_client:

            payload = {
                "symptom_text": "I have a bad headache and sensitivity to light."
            }
            headers = {"Authorization": "Bearer this_is_a_dummy_token"}

            print(f"[Test] Sending POST to api/chatbot/symptom with payload: {payload}")

            response = await async_client.post(
                "api/chatbot/symptom", json=payload, headers=headers
            )

            print(f"[Test] Received response status: {response.status_code}")
            print(f"[Test] Received response body: {response.text}")
            assert (
                response.status_code == 200
            ), f"Unexpected status code: {response.status_code}, Response: {response.text}"

            data = response.json()
            assert data["input_text"] == payload["symptom_text"]
            assert "TRIAGE_SCHEDULE" in data["analysis"]
            assert "migraine" in data["analysis"]
            assert data["triage_advice"] == "schedule_appointment"
            assert data.get("model_response") is not None

            try:
                model_resp_json = json.loads(data["model_response"])
                assert model_resp_json["object"] == "chat.completion"
                assert "google/gemini-2.0-flash-exp:free" in model_resp_json["model"]
            except json.JSONDecodeError:
                pytest.fail(
                    f"model_response was not a valid JSON string: {data['model_response']}"
                )

            print("\n[Result] Test POST /symptom passed with response:")
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
        print("[Cleanup] Restored original DB and Auth overrides.")
        print("--- Finished test_analyze_symptoms ---")
