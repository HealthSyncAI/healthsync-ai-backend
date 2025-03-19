import uuid

from database import update_appointment


class ProcessingUnit:
    def __init__(self, unit_id, data_pump_queue):
        self.unit_id = unit_id
        self.data_grid = {}  # In-memory data grid (simulated)
        self.data_pump_queue = data_pump_queue

    def process_request(self, request):
        """Handles incoming requests (e.g., schedule appointment)."""
        request_type = request["type"]

        if request_type == "schedule_appointment":
            return self.handle_schedule_appointment(request)
        else:
            return {"error": "Unknown request type"}

    def handle_schedule_appointment(self, request):
        """Simulates appointment scheduling logic."""
        patient_id = request["patient_id"]
        doctor_id = request["doctor_id"]
        appointment_time = request["appointment_time"]

        # ---  Chatbot Interaction (SIMULATED) ---
        symptoms = request.get("symptoms", "")
        chatbot_response = self.simulate_chatbot(symptoms)
        # ----------------------------------------

        appointment_id = str(uuid.uuid4())  # Generate a unique ID
        appointment_data = {
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "appointment_time": appointment_time,
            "symptoms": symptoms,
            "chatbot_response": chatbot_response,
        }

        # --- In-Memory Data Grid Update (SIMULATED) ---
        self.data_grid[appointment_id] = appointment_data
        print(f"PROCESSING UNIT {self.unit_id}: Cached appointment {appointment_id}")

        # --- Asynchronous Data Pump (to database) ---
        self.data_pump_queue.put(
            {
                "type": "update_appointment",
                "appointment_id": appointment_id,
                "appointment_data": appointment_data,
            }
        )

        return {
            "status": "success",
            "appointment_id": appointment_id,
            "chatbot_response": chatbot_response,
        }

    def simulate_chatbot(self, symptoms):
        """Simulates interaction with a chatbot."""
        if not symptoms:
            return "Please provide your symptoms."
        elif "fever" in symptoms.lower():
            return "It sounds like you might have a fever.  Please consider scheduling an appointment soon."
        else:
            return "Based on your symptoms, we recommend consulting with a doctor."


def data_pump_worker(data_pump_queue):
    """Continuously processes data pump updates."""
    while True:
        update_request = data_pump_queue.get()  # Blocking call
        if update_request["type"] == "update_appointment":
            update_appointment(
                update_request["appointment_id"], update_request["appointment_data"]
            )
        data_pump_queue.task_done()
