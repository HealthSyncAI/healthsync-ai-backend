class Event:
    """Base class for all events."""

    def __init__(self, timestamp=None):
        import datetime
        self.timestamp = timestamp or datetime.datetime.now()


class AppointmentRequested(Event):
    """Event triggered when a patient requests an appointment."""

    def __init__(self, patient_id, doctor_id, requested_time, symptoms, **kwargs):
        super().__init__(**kwargs)
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.requested_time = requested_time
        self.symptoms = symptoms


class DoctorAvailabilityChecked(Event):
    """Event triggered after checking doctor availability."""

    def __init__(self, request_id, doctor_id, available, **kwargs):
        super().__init__(**kwargs)
        self.request_id = request_id  # Correlation ID
        self.doctor_id = doctor_id
        self.available = available
        self.suggested_times = [] if available else ["2024-03-16 10:00", "2024-03-16 14:00"]


class AppointmentScheduled(Event):
    """Event triggered when an appointment is successfully scheduled."""

    def __init__(self, request_id, appointment_id, patient_id, doctor_id, appointment_time, **kwargs):
        super().__init__(**kwargs)
        self.request_id = request_id  # Correlation ID
        self.appointment_id = appointment_id
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.appointment_time = appointment_time


class AppointmentCreationFailed(Event):
    """Event when appointment creation fails"""

    def __init__(self, request_id, patient_id, doctor_id, reason, **kwargs):
        super().__init__(**kwargs)
        self.request_id = request_id
        self.patient_id = patient_id
        self.doctor_id = doctor_id
        self.reason = reason


class AppointmentReminderSent(Event):
    """Event triggered when a reminder is sent."""

    def __init__(self, appointment_id, patient_id, **kwargs):
        super().__init__(**kwargs)
        self.appointment_id = appointment_id
        self.patient_id = patient_id
