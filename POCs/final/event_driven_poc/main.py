# main.py
import events
from broker import EventBroker
import services
from functools import partial  # Import partial


def main():
    """Main function to run the simulation."""
    broker = EventBroker()

    # Subscribe event handlers (listeners) using partial
    broker.subscribe(
        events.AppointmentRequested,
        partial(services.check_doctor_availability, broker=broker),
    )
    broker.subscribe(
        events.DoctorAvailabilityChecked,
        partial(services.schedule_appointment, broker=broker),
    )
    broker.subscribe(
        events.AppointmentScheduled,
        partial(services.send_appointment_reminder, broker=broker),
    )
    broker.subscribe(
        events.AppointmentCreationFailed,
        partial(services.log_appointment_creation_failed, broker=broker),
    )

    # Simulate a patient requesting an appointment.
    request_event = events.AppointmentRequested(
        patient_id=123,
        doctor_id=2,  # Even ID, should be available
        requested_time="2024-03-15 10:00",
        symptoms="Fever, cough",
    )
    broker.publish(request_event)

    print("---")

    request_event2 = events.AppointmentRequested(
        patient_id=456,
        doctor_id=3,  # Odd ID, should be unavailable
        requested_time="2024-03-15 11:00",
        symptoms="Headache",
    )
    broker.publish(request_event2)


if __name__ == "__main__":
    main()
