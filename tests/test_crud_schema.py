import asyncio
from datetime import datetime

import pytest

from app.db.database import AsyncSessionLocal
from app.models.appointment import Appointment, AppointmentStatus
from app.models.chat_session import ChatSession
from app.models.health_record import HealthRecord
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_crud():
    async with AsyncSessionLocal() as session:
        # -------------------- CREATE --------------------
        # Create a doctor user
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
        # Create a patient user
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
        print("CREATE: Created doctor and patient users.")

        # Create an appointment
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_time=datetime(2025, 2, 10, 10, 0, 0),
            status=AppointmentStatus.scheduled,
            telemedicine_url="https://video.example.com/meet/12345",
        )
        session.add(appointment)
        await session.commit()
        await session.refresh(appointment)
        print("CREATE: Created Appointment:", appointment)

        # Create a health record
        health_record = HealthRecord(
            patient_id=patient.id,
            doctor_id=doctor.id,
            record_data='{"notes": "Patient presents with cough and fever. Triage advice: schedule a checkup."}',
        )
        session.add(health_record)
        await session.commit()
        await session.refresh(health_record)
        print("CREATE: Created Health Record:", health_record)

        # Create a chat session
        chat_session = ChatSession(
            patient_id=patient.id,
            input_text="I have a cough and slight fever.",
            voice_transcription=None,
            model_response='{"analysis": "suggests mild respiratory infection"}',
            triage_advice="Schedule a checkup and monitor symptoms.",
        )
        session.add(chat_session)
        await session.commit()
        await session.refresh(chat_session)
        print("CREATE: Created Chat Session:", chat_session)

        # -------------------- READ --------------------
        fetched_doctor = await session.get(User, doctor.id)
        fetched_patient = await session.get(User, patient.id)
        fetched_appointment = await session.get(Appointment, appointment.id)
        fetched_health_record = await session.get(HealthRecord, health_record.id)
        fetched_chat_session = await session.get(ChatSession, chat_session.id)

        assert fetched_doctor is not None and fetched_doctor.username == "dr_house"
        assert fetched_patient is not None and fetched_patient.username == "john_doe"
        assert fetched_appointment is not None
        assert fetched_health_record is not None
        assert fetched_chat_session is not None
        print("READ: Successfully fetched all records.")

        # -------------------- UPDATE --------------------
        # Update doctor's first name
        fetched_doctor.first_name = "Greg"
        await session.commit()
        await session.refresh(fetched_doctor)
        assert fetched_doctor.first_name == "Greg"
        print("UPDATE: Updated doctor's first name to:", fetched_doctor.first_name)

        # Update appointment status (assuming AppointmentStatus has a 'completed' value)
        fetched_appointment.status = AppointmentStatus.completed
        await session.commit()
        await session.refresh(fetched_appointment)
        assert fetched_appointment.status == AppointmentStatus.completed
        print("UPDATE: Updated appointment status to:", fetched_appointment.status)

        # -------------------- DELETE --------------------
        # Delete the chat session
        await session.delete(chat_session)
        await session.commit()
        deleted_chat_session = await session.get(ChatSession, chat_session.id)
        assert deleted_chat_session is None, "Chat session should be deleted"
        print("DELETE: Chat session deleted successfully.")

        # Delete the health record
        await session.delete(health_record)
        await session.commit()
        deleted_health_record = await session.get(HealthRecord, health_record.id)
        assert deleted_health_record is None, "Health record should be deleted"
        print("DELETE: Health record deleted successfully.")

        # Delete the appointment
        await session.delete(appointment)
        await session.commit()
        deleted_appointment = await session.get(Appointment, appointment.id)
        assert deleted_appointment is None, "Appointment should be deleted"
        print("DELETE: Appointment deleted successfully.")

        # Delete the users: doctor and patient
        await session.delete(doctor)
        await session.delete(patient)
        await session.commit()
        deleted_doctor = await session.get(User, doctor.id)
        deleted_patient = await session.get(User, patient.id)
        assert deleted_doctor is None, "Doctor should be deleted"
        assert deleted_patient is None, "Patient should be deleted"
        print("DELETE: Doctor and patient deleted successfully.")
