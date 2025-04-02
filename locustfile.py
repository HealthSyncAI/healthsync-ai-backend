import random

from locust import HttpUser, task, between

# --- Test Configuration ---
TEST_USERNAME = "johndoe"
TEST_PASSWORD = "YourSecurePassword"


class BackendUser(HttpUser):
    """
    Simulates a user interacting with the HealthSync AI backend.
    """
    wait_time = between(1, 3)
    token = None  # To store the JWT token after login

    def on_start(self):
        """
        Called when a Locust user starts. Used here for login.
        Each simulated user will try to log in once.
        """
        print(f"User starting... Attempting login for {TEST_USERNAME}")
        try:
            response = self.client.post(
                "/api/auth/login",
                data={"username": TEST_USERNAME, "password": TEST_PASSWORD}
            )
            response.raise_for_status()

            json_response = response.json()
            if "access_token" in json_response:
                self.token = json_response["access_token"]
                print("Login successful, token obtained.")
            else:
                print("Login failed: 'access_token' not in response.")
                response.failure("Login failed: No access token")

        except Exception as e:
            print(f"Login failed for {TEST_USERNAME}: {e}")

    @task(1)
    def health_check(self):
        """Task to hit the health check endpoint."""
        self.client.get("/health")

    @task(5)
    def chatbot_symptom_check(self):
        """Task to simulate a user sending symptoms to the chatbot."""
        if not self.token:
            print("Skipping chatbot task: No auth token.")
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        symptom_payload = {
            "symptom_text": f"Feeling unwell, slight headache and fatigue for {random.randint(1, 3)} days.",
            "room_number": None
        }
        self.client.post("/api/chatbot/symptom", json=symptom_payload, headers=headers, name="/api/chatbot/symptom")

    @task(3)
    def get_my_appointments(self):
        """Task to simulate fetching user's appointments."""
        if not self.token:
            print("Skipping get_appointments task: No auth token.")
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get("/api/appointment/my-appointments", headers=headers, name="/api/appointment/my-appointments")

    @task(2)
    def get_user_chats(self):
        """Task to simulate fetching user's chat history."""
        if not self.token:
            print("Skipping get_chats task: No auth token.")
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get("/api/chatbot/chats", headers=headers, name="/api/chatbot/chats")
