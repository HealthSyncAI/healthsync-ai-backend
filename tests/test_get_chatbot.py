import pytest
from datetime import datetime
from httpx import AsyncClient, ASGITransport
import json

from app.main import app
from app.db.database import get_db_session
from app.services.auth import AuthService


class DummyUser:
    id = 1
    username = "dummy_user"
    role = "patient"


async def dummy_get_current_user_method(*args, **kwargs):
    """Returns the dummy user object."""
    return DummyUser()


class DummyAuthService:
    """A dummy AuthService whose get_current_user returns a DummyUser, ignoring the token."""

    async def get_current_user(self, token: str = None):
        return await dummy_get_current_user_method()


def dummy_auth_service_provider():
    """Provides an instance of the DummyAuthService for dependency override."""
    return DummyAuthService()


class DummyChatRoomObj:
    def __init__(self, room_number):
        self.room_number = room_number


class DummyChatSessionObj:
    def __init__(
        self, id, input_text, model_response, triage_advice, created_at, chat_room
    ):
        self.id = id
        self.input_text = input_text
        self.model_response = model_response
        self.triage_advice = triage_advice
        self.created_at = created_at
        self.chat_room = chat_room

    @property
    def room_number(self):
        return self.chat_room.room_number if self.chat_room else None


class DummyResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return self

    def all(self):
        return self._items


class DummyDBSessionForChats:
    async def execute(self, query):
        room1 = DummyChatRoomObj(room_number=1)
        room2 = DummyChatRoomObj(room_number=2)
        simulated_db_result = [
            DummyChatSessionObj(
                id=3,
                input_text="Sore throat",
                model_response="Gargle salt water",
                triage_advice="Self-care",
                created_at=datetime(2025, 3, 2, 11, 0, 0),
                chat_room=room2,
            ),
            DummyChatSessionObj(
                id=1,
                input_text="Headache",
                model_response="Migraine?",
                triage_advice="Rest",
                created_at=datetime(2025, 3, 1, 10, 0, 0),
                chat_room=room1,
            ),
            DummyChatSessionObj(
                id=2,
                input_text="Feeling tired",
                model_response="Get sleep",
                triage_advice="Self-care",
                created_at=datetime(2025, 3, 1, 9, 0, 0),
                chat_room=room1,
            ),
        ]
        return DummyResult(simulated_db_result)


async def dummy_get_db_session():
    yield DummyDBSessionForChats()


@pytest.mark.asyncio
async def test_get_user_chats():
    """
    Test the /chats endpoint with corrected Auth (via override + dummy header)
    and DB mocking. Expects a grouped List[ChatRoomChats] response.
    Checks for 'model_response' key in output due to observed serialization behavior.
    """

    original_auth_override = app.dependency_overrides.get(AuthService)
    original_db_override = app.dependency_overrides.get(get_db_session)

    app.dependency_overrides[AuthService] = dummy_auth_service_provider
    app.dependency_overrides[get_db_session] = dummy_get_db_session

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as async_client:
            headers = {"Authorization": "Bearer this_is_a_dummy_token"}
            response = await async_client.get("api/chatbot/chats", headers=headers)

            assert (
                response.status_code == 200
            ), f"Unexpected status code: {response.status_code}, Response: {response.text}"
            data = response.json()

            assert isinstance(data, list), "Response is not a list."
            assert len(data) == 2, f"Expected 2 chat room groups, got {len(data)}"

            room1_group, room2_group = data[0], data[1]

            assert room1_group["room_number"] == 1
            assert len(room1_group["chats"]) == 2
            chat1_room1, chat2_room1 = room1_group["chats"][0], room1_group["chats"][1]

            print("\n--- Debugging chat1_room1 ---")
            print(chat1_room1)
            print("Keys:", chat1_room1.keys())
            print("--- End Debugging ---")
            assert (
                chat1_room1["id"] == 1 and chat1_room1["model_response"] == "Migraine?"
            )

            print("\n--- Debugging chat2_room1 ---")
            print(chat2_room1)
            print("Keys:", chat2_room1.keys())
            print("--- End Debugging ---")
            assert (
                chat2_room1["id"] == 2 and chat2_room1["model_response"] == "Get sleep"
            )

            assert room2_group["room_number"] == 2
            assert len(room2_group["chats"]) == 1
            chat1_room2 = room2_group["chats"][0]

            print("\n--- Debugging chat1_room2 ---")
            print(chat1_room2)
            print("Keys:", chat1_room2.keys())
            print("--- End Debugging ---")
            assert (
                chat1_room2["id"] == 3
                and chat1_room2["model_response"] == "Gargle salt water"
            )

            print(
                "\nTest GET /chats passed with expected grouped structure (using 'model_response' key):"
            )
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
