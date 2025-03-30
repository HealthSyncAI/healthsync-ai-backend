

import json

import pytest
from httpx import AsyncClient, ASGITransport

from app.db.database import TestAsyncSessionLocal
from app.main import app

from app.models.health_record import RecordType

from app.models.user import User, UserRole
from app.services.auth import AuthService



class DummyUser:

    def __init__(self, id, role: UserRole = UserRole.patient, username="dummy_user"):
        self.id = id
        self.role = role
        self.username = username
        self.first_name = "Dummy"
        self.last_name = "User"
        self.email = f"{username}@example.com"



async def dummy_get_current_user_method(user_id=1, role: UserRole = UserRole.patient, username="dummy_patient"):
    return DummyUser(id=user_id, role=role, username=username)


class DummyAuthService:
    _current_user_id = 1
    _current_user_role: UserRole = UserRole.patient
    _current_user_username = "dummy_patient"


    def set_user(self, user_id, role_str: str, username):
        self._current_user_id = user_id
        try:

            self._current_user_role = UserRole(role_str.lower())
        except ValueError:
            self._current_user_role = UserRole.patient
        self._current_user_username = username

    async def get_current_user(self, token: str = None):

        return await dummy_get_current_user_method(
            user_id=self._current_user_id,
            role=self._current_user_role,
            username=self._current_user_username
        )


_dummy_auth_service_instance = DummyAuthService()


def dummy_auth_service_provider():
    return _dummy_auth_service_instance



@pytest.fixture(scope="function")
async def setup_users_for_health_record():
    """Creates a patient and a doctor user in the test DB."""
    async with TestAsyncSessionLocal() as session:
        patient = User(
            username="hr_patient",
            email="hr_patient@example.com",
            hashed_password="testpassword",
            role=UserRole.patient,
            first_name="HealthRec",
            last_name="Patient"
        )
        doctor = User(
            username="hr_doctor",
            email="hr_doctor@example.com",
            hashed_password="testpassword",
            role=UserRole.doctor,
            first_name="HealthRec",
            last_name="Doctor",
            specialization="GP"
        )
        session.add_all([patient, doctor])
        await session.commit()
        await session.refresh(patient)
        await session.refresh(doctor)
        print(f"SETUP: Created Patient ID: {patient.id}, Doctor ID: {doctor.id}")
        return {"patient_id": patient.id, "doctor_id": doctor.id}


@pytest.mark.asyncio
async def test_health_record_endpoints(setup_users_for_health_record):
    """
    Tests creating health records (generic and doctor notes),
    fetching records for a patient, and fetching a specific record.
    Checks permissions for creating and accessing records.
    Relies on the actual test DB managed by conftest.py.
    Mocks authentication.
    """
    user_ids = await setup_users_for_health_record
    patient_id = user_ids["patient_id"]
    doctor_id = user_ids["doctor_id"]

    original_auth_override = app.dependency_overrides.get(AuthService)

    app.dependency_overrides[AuthService] = dummy_auth_service_provider

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        headers = {"Authorization": "Bearer dummy_token"}
        record_ids = {}


        print("\n--- Testing POST /api/health-record/ (by Doctor) ---")

        _dummy_auth_service_instance.set_user(doctor_id, "doctor", "hr_doctor")

        generic_record_payload = {
            "title": "Initial Triage Record",
            "summary": "Patient reported headache via chat.",
            "record_type": RecordType.at_triage.value,
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "symptoms": [{"name": "headache", "severity": 5, "duration": "2 hours"}],
            "triage_recommendation": "schedule_appointment"
        }

        response_post_generic = await client.post("/api/health-record/", json=generic_record_payload, headers=headers)
        print(f"POST Generic Response Status: {response_post_generic.status_code}")
        try:
            response_data_generic = response_post_generic.json()
            print(f"POST Generic Response Data: {json.dumps(response_data_generic, indent=2)}")
        except json.JSONDecodeError:
            print(f"POST Generic Response Text: {response_post_generic.text}")
            response_data_generic = None


        assert response_post_generic.status_code == 201, f"Expected 201, got {response_post_generic.status_code}. Response: {response_post_generic.text}"

        assert response_data_generic["patient_id"] == patient_id
        assert response_data_generic["doctor_id"] == doctor_id
        assert response_data_generic["record_type"] == RecordType.at_triage.value
        assert "id" in response_data_generic
        record_ids["generic"] = response_data_generic["id"]
        print(f"Generic health record created successfully. ID: {record_ids['generic']}")


        print("\n--- Testing POST /api/health-record/ (by Patient - Forbidden) ---")

        _dummy_auth_service_instance.set_user(patient_id, "patient", "hr_patient")
        forbidden_payload = generic_record_payload.copy()
        forbidden_payload["title"] = "Patient Self-Record Attempt"
        forbidden_payload["patient_id"] = patient_id

        response_post_forbidden = await client.post("/api/health-record/", json=forbidden_payload, headers=headers)
        print(f"POST Forbidden Response Status: {response_post_forbidden.status_code}")









        assert response_post_forbidden.status_code == 201, f"Expected 201 (patient creating for self), got {response_post_forbidden.status_code}. Detail: {response_post_forbidden.text}"
        print("Patient creating record for self correctly allowed (status 201).")

        if response_post_forbidden.status_code == 201:
            record_ids["patient_self_generic"] = response_post_forbidden.json()["id"]


        print("\n--- Testing POST /api/health-record/doctor-note ---")

        _dummy_auth_service_instance.set_user(doctor_id, "doctor", "hr_doctor")

        doctor_note_payload = {
            "title": "Consultation Note",
            "summary": "Discussed symptoms, recommended rest.",
            "patient_id": patient_id,
            "symptoms": [{"name": "headache", "severity": 3, "description": "tension-type"}],
            "diagnosis": [{"name": "Tension headache", "icd10_code": "G44.2"}],
            "treatment_plan": [{"description": "Continue rest, follow up if worsens", "follow_up": "PRN"}],
            "medication": [{"name": "Ibuprofen", "dosage": "400mg", "frequency": "As needed"}]
        }
        response_post_note = await client.post("/api/health-record/doctor-note", json=doctor_note_payload,
                                               headers=headers)
        print(f"POST Note Response Status: {response_post_note.status_code}")
        try:
            response_data_note = response_post_note.json()
            print(f"POST Note Response Data: {json.dumps(response_data_note, indent=2)}")
        except json.JSONDecodeError:
            print(f"POST Note Response Text: {response_post_note.text}")
            response_data_note = None

        assert response_post_note.status_code == 201, f"Expected 201, got {response_post_note.status_code}. Response: {response_post_note.text}"
        assert response_data_note["patient_id"] == patient_id
        assert response_data_note["doctor_id"] == doctor_id
        assert response_data_note["record_type"] == RecordType.doctor_note.value
        assert "id" in response_data_note
        record_ids["note"] = response_data_note["id"]
        print(f"Doctor note created successfully. ID: {record_ids['note']}")


        print(f"\n--- Testing GET /api/health-record/patient/{patient_id} ---")

        _dummy_auth_service_instance.set_user(patient_id, "patient", "hr_patient")
        response_get_patient_recs = await client.get(f"/api/health-record/patient/{patient_id}", headers=headers)
        print(f"GET Patient Recs Response Status: {response_get_patient_recs.status_code}")
        try:
            response_data_patient_recs = response_get_patient_recs.json()
            print(f"GET Patient Recs Response Data: {json.dumps(response_data_patient_recs, indent=2)}")
        except json.JSONDecodeError:
            print(f"GET Patient Recs Response Text: {response_get_patient_recs.text}")
            response_data_patient_recs = None

        assert response_get_patient_recs.status_code == 200, f"Expected 200, got {response_get_patient_recs.status_code}. Response: {response_get_patient_recs.text}"
        assert isinstance(response_data_patient_recs, list)

        assert len(response_data_patient_recs) == 3, f"Expected 3 records, found {len(response_data_patient_recs)}"
        found_ids = {rec["id"] for rec in response_data_patient_recs}
        assert record_ids["generic"] in found_ids, "Generic record (by doctor) not found"
        assert record_ids["note"] in found_ids, "Doctor note record not found"
        assert record_ids["patient_self_generic"] in found_ids, "Generic record (by patient) not found"
        print("Patient records fetched successfully.")


        note_id_to_fetch = record_ids["note"]
        print(f"\n--- Testing GET /api/health-record/{note_id_to_fetch} ---")

        _dummy_auth_service_instance.set_user(patient_id, "patient", "hr_patient")
        response_get_specific = await client.get(f"/api/health-record/{note_id_to_fetch}", headers=headers)
        print(f"GET Specific Rec Response Status: {response_get_specific.status_code}")
        try:
            response_data_specific = response_get_specific.json()
            print(f"GET Specific Rec Response Data: {json.dumps(response_data_specific, indent=2)}")
        except json.JSONDecodeError:
            print(f"GET Specific Rec Response Text: {response_get_specific.text}")
            response_data_specific = None

        assert response_get_specific.status_code == 200, f"Expected 200, got {response_get_specific.status_code}. Response: {response_get_specific.text}"
        assert response_data_specific["id"] == note_id_to_fetch
        assert response_data_specific["title"] == "Consultation Note"
        print("Specific health record fetched successfully by patient.")


    if original_auth_override:
        app.dependency_overrides[AuthService] = original_auth_override
    else:
        app.dependency_overrides.pop(AuthService, None)
