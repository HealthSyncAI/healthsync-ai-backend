import queue
import threading
import time

from processing_unit import ProcessingUnit, data_pump_worker
import database


def main():
    # --- Setup ---
    data_pump_queue = queue.Queue()
    data_pump_thread = threading.Thread(
        target=data_pump_worker, args=(data_pump_queue,), daemon=True
    )
    data_pump_thread.start()

    num_processing_units = 3  # Simulate multiple processing units
    processing_units = [
        ProcessingUnit(i, data_pump_queue) for i in range(num_processing_units)
    ]

    # --- Simulate incoming requests ---
    requests = [
        {
            "type": "schedule_appointment",
            "patient_id": "user123",
            "doctor_id": "doc456",
            "appointment_time": "2024-07-29 10:00",
            "symptoms": "Fever and cough",
        },
        {
            "type": "schedule_appointment",
            "patient_id": "user789",
            "doctor_id": "doc789",
            "appointment_time": "2024-07-30 14:00",
            "symptoms": "Headache",
        },
        {
            "type": "schedule_appointment",
            "patient_id": "user123",
            "doctor_id": "doc456",
            "appointment_time": "2024-07-29 10:00",
            "symptoms": "Fever and cough",
        },
    ]

    def send_request(request):
        # Simple Round Robin
        target_unit = processing_units[send_request.counter % len(processing_units)]
        send_request.counter += 1
        return target_unit.process_request(request)

    send_request.counter = 0  # init static variable

    # --- Process requests ---
    for request in requests:
        # Simulate routing (round-robin in this simple example)
        response = send_request(request)
        print(f"FRONTEND: Received response: {response}")

    # --- Wait for data pump to finish (in a real system, this would be more sophisticated) ---
    time.sleep(2)  # Give the data pump some time to process
    print("DONE")
    print("Final Database:", database.database_data)


if __name__ == "__main__":
    main()
