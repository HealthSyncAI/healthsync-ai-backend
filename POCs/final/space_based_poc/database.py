database_data = {
    "appointments": {},  # {appointment_id: {patient_id, doctor_id, time, ...}}
    "users": {},  # {user_id: {name, ...}}
}


def update_appointment(appointment_id, appointment_data):
    """Simulates updating an appointment in the database."""
    database_data["appointments"][appointment_id] = appointment_data
    print(f"DATABASE: Updated appointment {appointment_id}: {appointment_data}")


def get_user(user_id):
    """Simulates retrieving user data"""
    return database_data["users"].get(user_id)
