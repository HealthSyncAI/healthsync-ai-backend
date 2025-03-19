import events
import services
from broker import EventBroker


def main():
    """Main function to run the simulation."""
    broker = EventBroker()

    # Subscribe event handlers (listeners)
    broker.subscribe(events.AppointmentRequested, services.check_doctor_availability)
    broker.subscribe(events.DoctorAvailabilityChecked, services.schedule_appointment)
    broker.subscribe(events.AppointmentScheduled, services.send_appointment_reminder)
    broker.subscribe(events.AppointmentCreationFailed, services.log_appointment_creation_failed)

    # Simulate a patient requesting an appointment.
    request_event = events.AppointmentRequested(
        patient_id=123,
        doctor_id=2,  # Even ID, should be available
        requested_time="2024-03-15 10:00",
        symptoms="Fever, cough"
    )
    broker.publish(request_event)

    print("---")

    request_event2 = events.AppointmentRequested(
        patient_id=456,
        doctor_id=3,  # Odd ID, should be unavailable
        requested_time="2024-03-15 11:00",
        symptoms="Headache"
    )
    broker.publish(request_event2)


if __name__ == "__main__":
    main()
