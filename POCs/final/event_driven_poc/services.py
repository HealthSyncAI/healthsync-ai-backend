import uuid

from events import (
    DoctorAvailabilityChecked,
    AppointmentScheduled,
    AppointmentCreationFailed,
    AppointmentReminderSent,
)


def check_doctor_availability(event, broker):
    """Simulates checking doctor availability."""
    print(
        f"Checking availability for doctor {event.doctor_id} at {event.requested_time}..."
    )
    # In a real system, this would query a database or external service.
    available = event.doctor_id % 2 == 0  # Simulate: Even doctor IDs are available.
    request_id = event.timestamp.strftime(
        "%Y%m%d%H%M%S%f"
    )  # Use event timestamp for request ID
    availability_event = DoctorAvailabilityChecked(
        request_id=request_id, doctor_id=event.doctor_id, available=available
    )
    broker.publish(availability_event)


def schedule_appointment(event, broker):
    """Simulates scheduling an appointment."""
    if event.available:
        print(f"Scheduling appointment for request {event.request_id}...")
        # Simulate database interaction.
        appointment_id = str(uuid.uuid4())
        appointment_time = (
            event.suggested_times[0]
            if len(event.suggested_times) > 0
            else "2024-03-15 11:00"
        )  # Use available slot, or default
        scheduled_event = AppointmentScheduled(
            request_id=event.request_id,
            appointment_id=appointment_id,
            patient_id=123,
            doctor_id=event.doctor_id,
            appointment_time=appointment_time,
        )  # Use available slot.
        broker.publish(scheduled_event)
    else:
        print(
            f"Cannot schedule the appointment. Doctor {event.doctor_id} is not available."
        )
        failed_event = AppointmentCreationFailed(
            request_id=event.request_id,
            patient_id=123,
            doctor_id=event.doctor_id,
            reason="Doctor not available",
        )
        broker.publish(failed_event)


def send_appointment_reminder(event, broker):
    """Simulates sending an appointment reminder (we just log it)."""
    print(
        f"Sending reminder for appointment {event.appointment_id} to patient {event.patient_id}..."
    )
    # In a real system, this might send an email, SMS, or push notification.
    reminder_event = AppointmentReminderSent(
        appointment_id=event.appointment_id, patient_id=event.patient_id
    )
    broker.publish(reminder_event)


def log_appointment_creation_failed(event, broker):
    """log appointment creation failed"""
    print(
        f"Appointment creation failed: Patient: {event.patient_id}, Doctor: {event.doctor_id}, Reason: {event.reason}"
    )
