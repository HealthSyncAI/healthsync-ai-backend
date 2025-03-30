from datetime import datetime

import pytest

from app.db.database import TestAsyncSessionLocal
from app.models.appointment import Appointment, AppointmentStatus
from app.models.chat_room import ChatRoom
from app.models.chat_session import ChatSession
from app.models.health_record import HealthRecord, RecordType
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_crud():
    """
    Tests basic CRUD (Create, Read, Update, Delete) operations
    for the main models against the test database.
    """
    async with TestAsyncSessionLocal() as session:
        print("\n--- Starting CREATE Phase ---")

        doctor = User(
            username="dr_house",
            email="house@example.com",
            hashed_password="hashedsecret",
            role=UserRole.doctor,
            first_name="Gregory",
            last_name="House",
            specialization="Diagnostics",
            qualifications="MD, Nephrology",
            is_available=True,
        )

        patient = User(
            username="john_doe",
            email="john@example.com",
            hashed_password="hashedpassword",
            role=UserRole.patient,
            first_name="John",
            last_name="Doe",
        )
        session.add_all([doctor, patient])
        await session.commit()

        await session.refresh(doctor)
        await session.refresh(patient)
        print(f"CREATE: Created Doctor ID: {doctor.id}, Patient ID: {patient.id}")

        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            start_time=datetime(2025, 2, 10, 10, 0, 0),
            end_time=datetime(2025, 2, 10, 11, 0, 0),
            status=AppointmentStatus.scheduled,
            telemedicine_url="https://video.example.com/meet/12345",
        )
        session.add(appointment)
        await session.commit()
        await session.refresh(appointment)
        print(f"CREATE: Created Appointment ID: {appointment.id}")

        health_record = HealthRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            record_type=RecordType.at_triage,
            title="Initial Consultation",
            summary="Patient presents with cough and fever.",
            symptoms=[
                {"name": "cough", "severity": "mild"},
                {"name": "fever", "severity": "moderate"},
            ],
            diagnosis=[
                {
                    "name": "Acute upper respiratory infection, unspecified",
                    "icd10_code": "J06.9",
                }
            ],
            treatment_plan=[{"description": "Rest at home", "duration": "3 days"}],
            medication=[
                {"name": "Paracetamol", "dosage": "500mg", "frequency": "3 times a day"}
            ],
            triage_recommendation="Schedule a checkup",
            confidence_score=0.85,
        )
        session.add(health_record)
        await session.commit()
        await session.refresh(health_record)
        print(f"CREATE: Created Health Record ID: {health_record.id}")

        chat_room = ChatRoom(patient_id=patient.id, room_number=1)
        session.add(chat_room)
        await session.commit()
        await session.refresh(chat_room)
        print(
            f"CREATE: Created Chat Room ID: {chat_room.id} for Patient ID: {patient.id}"
        )

        chat_session = ChatSession(
            patient_id=patient.id,
            chat_room_id=chat_room.id,
            input_text="I have a cough and slight fever.",
            voice_transcription=None,
            model_response='{"analysis": "suggests mild respiratory infection"}',
            triage_advice="Schedule a checkup and monitor symptoms.",
        )
        session.add(chat_session)
        await session.commit()
        await session.refresh(chat_session)
        print(
            f"CREATE: Created Chat Session ID: {chat_session.id} in Room ID: {chat_room.id}"
        )
        print("--- CREATE Phase Complete ---")

        print("\n--- Starting READ Phase ---")
        fetched_doctor = await session.get(User, doctor.id)
        fetched_patient = await session.get(User, patient.id)
        fetched_appointment = await session.get(Appointment, appointment.id)
        fetched_health_record = await session.get(HealthRecord, health_record.id)
        fetched_chat_session = await session.get(ChatSession, chat_session.id)

        assert fetched_doctor is not None, "Doctor should be found"
        assert fetched_doctor.username == "dr_house"
        assert fetched_patient is not None, "Patient should be found"
        assert fetched_patient.username == "john_doe"
        assert fetched_appointment is not None, "Appointment should be found"
        assert fetched_health_record is not None, "Health record should be found"
        assert fetched_chat_session is not None, "Chat session should be found"
        assert (
            fetched_chat_session.chat_room_id == chat_room.id
        ), "Chat session should link to correct room"
        print("READ: Successfully fetched all created records.")
        print("--- READ Phase Complete ---")

        print("\n--- Starting UPDATE Phase ---")

        fetched_doctor.first_name = "Greg"

        await session.commit()

        await session.refresh(fetched_doctor)
        assert fetched_doctor.first_name == "Greg"
        print(f"UPDATE: Updated doctor's first name to: {fetched_doctor.first_name}")

        fetched_appointment.status = AppointmentStatus.completed
        await session.commit()
        await session.refresh(fetched_appointment)
        assert fetched_appointment.status == AppointmentStatus.completed
        print(
            f"UPDATE: Updated appointment status to: {fetched_appointment.status.value}"
        )
        print("--- UPDATE Phase Complete ---")

        print("\n--- Starting DELETE Phase ---")

        chat_session_id = chat_session.id
        await session.delete(chat_session)
        await session.commit()
        deleted_chat_session = await session.get(ChatSession, chat_session_id)
        assert deleted_chat_session is None, "Chat session should be deleted"
        print(f"DELETE: Chat session ID {chat_session_id} deleted successfully.")

        health_record_id = health_record.id
        await session.delete(health_record)
        await session.commit()
        deleted_health_record = await session.get(HealthRecord, health_record_id)
        assert deleted_health_record is None, "Health record should be deleted"
        print(f"DELETE: Health record ID {health_record_id} deleted successfully.")

        appointment_id = appointment.id
        await session.delete(appointment)
        await session.commit()
        deleted_appointment = await session.get(Appointment, appointment_id)
        assert deleted_appointment is None, "Appointment should be deleted"
        print(f"DELETE: Appointment ID {appointment_id} deleted successfully.")

        chat_room_id = chat_room.id
        await session.delete(chat_room)
        await session.commit()
        deleted_chat_room = await session.get(ChatRoom, chat_room_id)
        assert deleted_chat_room is None, "Chat room should be deleted"
        print(f"DELETE: Chat room ID {chat_room_id} deleted successfully.")

        doctor_id = doctor.id
        patient_id = patient.id
        await session.delete(doctor)
        await session.delete(patient)
        await session.commit()
        deleted_doctor = await session.get(User, doctor_id)
        deleted_patient = await session.get(User, patient_id)
        assert deleted_doctor is None, "Doctor should be deleted"
        assert deleted_patient is None, "Patient should be deleted"
        print(
            f"DELETE: Doctor ID {doctor_id} and Patient ID {patient_id} deleted successfully."
        )
        print("--- DELETE Phase Complete ---")
