

import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone
import json

from app.main import app
from app.db.database import TestAsyncSessionLocal
from app.models.user import User, UserRole
from app.models.appointment import Appointment, AppointmentStatus
from app.services.auth import AuthService
from app.services import health_record as health_record_service 


class DummyUser:
    def __init__(self, id, role="patient", username="dummy_user"):
        self.id = id
        self.role = role
        self.username = username
        
        self.first_name = "Dummy"
        self.last_name = "User"
        self.email = f"{username}@example.com"
        self.specialization = "Testing" if role == "doctor" else None
        self.is_available = True if role == "doctor" else None
        self.qualifications = "MD" if role == "doctor" else None

async def dummy_get_current_user_method(user_id=1, role="patient", username="dummy_patient"):
    """Returns a customizable dummy user."""
    return DummyUser(id=user_id, role=role, username=username)

class DummyAuthService:
    """A dummy AuthService whose get_current_user returns a DummyUser."""
    _current_user_id = 1
    _current_user_role = "patient"
    _current_user_username = "dummy_patient"

    def set_user(self, user_id, role, username):
        DummyAuthService._current_user_id = user_id
        DummyAuthService._current_user_role = role
        DummyAuthService._current_user_username = username

    async def get_current_user(self, token: str = None):
         
        return await dummy_get_current_user_method(
            user_id=self._current_user_id,
            role=self._current_user_role,
            username=self._current_user_username
        )

_dummy_auth_service_instance = DummyAuthService()

def dummy_auth_service_provider():
    """Provides the singleton instance of the DummyAuthService."""
    return _dummy_auth_service_instance


async def mock_create_triage_record(*args, **kwargs):
    print("Mocked create_triage_record_from_chats called, doing nothing.")
    return None


@pytest.fixture(scope="function")
async def setup_users_for_appointment():
    """Creates a patient and a doctor user in the test DB."""
    async with TestAsyncSessionLocal() as session:
        
        patient = User(
            username="appt_patient",
            email="appt_patient@example.com",
            hashed_password="testpassword", 
            role=UserRole.patient,
            first_name="Appt",
            last_name="Patient"
        )
        doctor = User(
            username="appt_doctor",
            email="appt_doctor@example.com",
            hashed_password="testpassword",
            role=UserRole.doctor,
            first_name="Appt",
            last_name="Doctor",
            specialization="Cardiology",
            qualifications="MD, FACC",
            is_available=True
        )
        session.add_all([patient, doctor])
        await session.commit()
        await session.refresh(patient)
        await session.refresh(doctor)
        print(f"SETUP: Created Patient ID: {patient.id}, Doctor ID: {doctor.id}")
        return {"patient_id": patient.id, "doctor_id": doctor.id}


@pytest.mark.asyncio
async def test_appointment_endpoints(setup_users_for_appointment, monkeypatch):
    """
    Tests appointment scheduling, fetching related health records,
    listing doctors, and fetching doctor details.
    Relies on the actual test DB managed by conftest.py and setup_users_for_appointment.
    Mocks authentication and the automatic triage record creation.
    """
    
    user_ids = await setup_users_for_appointment
    
    patient_id = user_ids["patient_id"]
    doctor_id = user_ids["doctor_id"]

    original_auth_override = app.dependency_overrides.get(AuthService)
    app.dependency_overrides[AuthService] = dummy_auth_service_provider

    
    monkeypatch.setattr(health_record_service, "create_triage_record_from_chats", mock_create_triage_record)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        headers = {"Authorization": "Bearer dummy_token"} 

        
        print("\n--- Testing POST /api/appointment/ ---")
        
        _dummy_auth_service_instance.set_user(patient_id, "patient", "appt_patient")

        appointment_payload = {
            "doctor_id": doctor_id,
            "start_time": datetime(2025, 4, 15, 14, 0, 0, tzinfo=timezone.utc).isoformat(),
            "end_time": datetime(2025, 4, 15, 14, 30, 0, tzinfo=timezone.utc).isoformat(),
            "telemedicine_url": "https://meet.example/appt123"
        }
        response_post = await client.post("/api/appointment/", json=appointment_payload, headers=headers)
        print(f"POST Response Status: {response_post.status_code}")
        try:
            response_data_post = response_post.json()
            print(f"POST Response Data: {json.dumps(response_data_post, indent=2)}")
        except json.JSONDecodeError:
             print(f"POST Response Text: {response_post.text}")
             response_data_post = None

        assert response_post.status_code == 201, f"Expected 201, got {response_post.status_code}. Response: {response_post.text}"
        assert response_data_post["patient_id"] == patient_id
        assert response_data_post["doctor_id"] == doctor_id
        assert response_data_post["status"] == AppointmentStatus.scheduled.value
        assert "id" in response_data_post
        appointment_id = response_data_post["id"]
        print(f"Appointment scheduled successfully. ID: {appointment_id}")

        
        print(f"\n--- Testing GET /api/appointment/{appointment_id}/health-records ---")
        
        _dummy_auth_service_instance.set_user(doctor_id, "doctor", "appt_doctor")
        response_get_hr = await client.get(f"/api/appointment/{appointment_id}/health-records", headers=headers)
        print(f"GET HR Response Status: {response_get_hr.status_code}")
        try:
            response_data_hr = response_get_hr.json()
            print(f"GET HR Response Data: {json.dumps(response_data_hr, indent=2)}")
        except json.JSONDecodeError:
             print(f"GET HR Response Text: {response_get_hr.text}")
             response_data_hr = None

        assert response_get_hr.status_code == 200, f"Expected 200, got {response_get_hr.status_code}. Response: {response_get_hr.text}"
        assert isinstance(response_data_hr, list)
        
        assert len(response_data_hr) == 0, "Expected empty health records list due to mocking"
        print("Health records fetched successfully (expected empty list).")

        
        print("\n--- Testing GET /api/appointment/doctors ---")
        
        _dummy_auth_service_instance.set_user(patient_id, "patient", "appt_patient")
        response_get_doctors = await client.get("/api/appointment/doctors", headers=headers, params={"specialization": "Cardiology"})
        print(f"GET Doctors Response Status: {response_get_doctors.status_code}")
        try:
            response_data_doctors = response_get_doctors.json()
            print(f"GET Doctors Response Data: {json.dumps(response_data_doctors, indent=2)}")
        except json.JSONDecodeError:
             print(f"GET Doctors Response Text: {response_get_doctors.text}")
             response_data_doctors = None

        assert response_get_doctors.status_code == 200, f"Expected 200, got {response_get_doctors.status_code}. Response: {response_get_doctors.text}"
        assert isinstance(response_data_doctors, list)
        assert len(response_data_doctors) > 0, "Expected at least one doctor"
        found_doctor = next((d for d in response_data_doctors if d["id"] == doctor_id), None)
        assert found_doctor is not None, "Created doctor not found in the list"
        assert found_doctor["specialization"] == "Cardiology"
        assert found_doctor["first_name"] == "Appt"
        print("Doctors listed successfully.")

        
        print(f"\n--- Testing GET /api/appointment/doctors/{doctor_id} ---")
        
        response_get_doctor_detail = await client.get(f"/api/appointment/doctors/{doctor_id}", headers=headers)
        print(f"GET Doctor Detail Response Status: {response_get_doctor_detail.status_code}")
        try:
            response_data_doctor_detail = response_get_doctor_detail.json()
            print(f"GET Doctor Detail Response Data: {json.dumps(response_data_doctor_detail, indent=2)}")
        except json.JSONDecodeError:
             print(f"GET Doctor Detail Response Text: {response_get_doctor_detail.text}")
             response_data_doctor_detail = None

        assert response_get_doctor_detail.status_code == 200, f"Expected 200, got {response_get_doctor_detail.status_code}. Response: {response_get_doctor_detail.text}"
        assert response_data_doctor_detail["id"] == doctor_id
        assert response_data_doctor_detail["email"] == "appt_doctor@example.com"
        assert response_data_doctor_detail["specialization"] == "Cardiology"
        assert "expertise_areas" in response_data_doctor_detail 
        assert "languages" in response_data_doctor_detail
        print("Doctor details fetched successfully.")

    
    if original_auth_override:
        app.dependency_overrides[AuthService] = original_auth_override
    else:
        app.dependency_overrides.pop(AuthService, None)