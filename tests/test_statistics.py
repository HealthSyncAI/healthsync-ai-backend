# File: tests/test_statistics.py

import pytest
from httpx import AsyncClient, ASGITransport
import json
from datetime import datetime, timezone

from app.main import app
from app.db.database import TestAsyncSessionLocal
from app.models.user import User, UserRole
from app.models.appointment import Appointment, AppointmentStatus
from app.models.chat_room import ChatRoom
from app.models.chat_session import ChatSession
from app.models.health_record import HealthRecord, RecordType
from app.api.schemas.statistics import UsageStatistics # To check keys

# No Auth mock needed for statistics endpoint based on current implementation
# but we can keep the setup for consistency or future changes.
from app.services.auth import AuthService
class DummyUser: # Minimal dummy user if needed
    id=999
    role="admin" # Or any role
    username="stats_tester"

async def dummy_get_current_user_method(): return DummyUser()
class DummyAuthService:
    async def get_current_user(self, token: str = None): return await dummy_get_current_user_method()
_dummy_auth_service_instance = DummyAuthService()
def dummy_auth_service_provider(): return _dummy_auth_service_instance


@pytest.fixture(scope="function")
async def setup_data_for_statistics():
    """Populates the test DB with various records for statistics calculation."""
    async with TestAsyncSessionLocal() as session:
        # Create Users
        p1 = User(username="stat_p1", email="stat_p1@example.com", hashed_password="p", role=UserRole.patient)
        p2 = User(username="stat_p2", email="stat_p2@example.com", hashed_password="p", role=UserRole.patient)
        d1 = User(username="stat_d1", email="stat_d1@example.com", hashed_password="d", role=UserRole.doctor)
        session.add_all([p1, p2, d1])
        await session.commit()
        await session.refresh(p1)
        await session.refresh(p2)
        await session.refresh(d1)
        print(f"SETUP: Users created: p1={p1.id}, p2={p2.id}, d1={d1.id}")

        # Create Appointments
        appt1 = Appointment(patient_id=p1.id, doctor_id=d1.id, start_time=datetime.now(timezone.utc), end_time=datetime.now(timezone.utc), status=AppointmentStatus.scheduled)
        appt2 = Appointment(patient_id=p2.id, doctor_id=d1.id, start_time=datetime.now(timezone.utc), end_time=datetime.now(timezone.utc), status=AppointmentStatus.completed)
        session.add_all([appt1, appt2])
        await session.commit()
        print("SETUP: Appointments created.")

        # Create Chat Rooms and Sessions
        room1 = ChatRoom(patient_id=p1.id, room_number=1)
        session.add(room1)
        await session.commit()
        await session.refresh(room1)
        chat1 = ChatSession(patient_id=p1.id, chat_room_id=room1.id, input_text="Hi", model_response="Hello")
        chat2 = ChatSession(patient_id=p1.id, chat_room_id=room1.id, input_text="Symptom?", model_response="AI Answer")
        session.add_all([chat1, chat2])
        await session.commit()
        print("SETUP: Chat Room and Sessions created.")

        # Create Health Records
        hr1 = HealthRecord(patient_id=p1.id, doctor_id=d1.id, record_type=RecordType.at_triage, title="Triage 1")
        hr2 = HealthRecord(patient_id=p2.id, doctor_id=d1.id, record_type=RecordType.doctor_note, title="Note 1")
        hr3 = HealthRecord(patient_id=p1.id, doctor_id=d1.id, record_type=RecordType.doctor_note, title="Note 2")
        session.add_all([hr1, hr2, hr3])
        await session.commit()
        print("SETUP: Health Records created.")

        return {"patient_count": 2, "doctor_count": 1, "appt_count": 2, "chat_count": 2, "hr_count": 3, "triage_count": 1, "note_count": 2}

@pytest.mark.asyncio
async def test_get_usage_statistics(setup_data_for_statistics):
    """
    Tests the /statistics endpoint.
    Relies on data populated in the test DB by the setup_data_for_statistics fixture.
    """
    # ***** CORRECTED LINE *****
    expected_counts = await setup_data_for_statistics
    # *************************

    # --- No Auth override needed, but keeping structure ---
    original_auth_override = app.dependency_overrides.get(AuthService)
    # app.dependency_overrides[AuthService] = dummy_auth_service_provider # Currently not needed

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        headers = {"Authorization": "Bearer dummy_token"} # Not strictly needed now

        print("\n--- Testing GET /api/statistics/ ---")
        response = await client.get("/api/statistics/", headers=headers)
        print(f"GET Statistics Response Status: {response.status_code}")
        try:
            response_data = response.json()
            print(f"GET Statistics Response Data: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
             print(f"GET Statistics Response Text: {response.text}")
             response_data = None

        assert response.status_code == 200, f"Expected 200, got {response.status_code}. Response: {response.text}"
        assert isinstance(response_data, dict)

        # Check all expected keys are present
        expected_keys = set(UsageStatistics.model_fields.keys())
        assert set(response_data.keys()) == expected_keys, "Response keys do not match UsageStatistics schema"

        # Verify counts against the setup data
        assert response_data["total_users"] == expected_counts["patient_count"] + expected_counts["doctor_count"]
        assert response_data["total_patients"] == expected_counts["patient_count"]
        assert response_data["total_doctors"] == expected_counts["doctor_count"]
        assert response_data["total_appointments"] == expected_counts["appt_count"]
        assert response_data["total_chat_sessions"] == expected_counts["chat_count"]
        assert response_data["total_health_records"] == expected_counts["hr_count"]
        assert response_data["total_triage_records"] == expected_counts["triage_count"]
        assert response_data["total_doctor_notes"] == expected_counts["note_count"]

        print("Usage statistics fetched and validated successfully.")

    # Cleanup dependency overrides (if any were set)
    if original_auth_override:
        app.dependency_overrides[AuthService] = original_auth_override
    else:
        # app.dependency_overrides.pop(AuthService, None) # Uncomment if override was used
        pass