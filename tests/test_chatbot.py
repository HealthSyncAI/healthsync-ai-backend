import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_chatbot_symptom_endpoint():
    """
    Test the /chatbot/symptom endpoint:
    - Provide a valid symptom text with a dummy authentication token.
    - Expect a valid structured response containing:
        - input_text: matching the payload.
        - analysis: generated output using the DialoGPT pipeline.
        - model_response: the raw pipeline output.
    """
    # Use ASGITransport so that the test runs in memory.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Prepare the payload with a sample symptom.
        payload = {"symptom_text": "I have a severe headache and nausea."}

        # Provide a dummy auth header; the get_current_user dependency is overridden.
        headers = {"Authorization": "Bearer test-token"}
        response = await client.post("/api/chatbot/symptom", json=payload, headers=headers)

        # Ensure that the response status is 200 (OK).
        assert response.status_code == 200, f"Expected status 200, got {response.status_code}"

        json_data = response.json()

        # Validate response structure.
        assert json_data.get("input_text") == payload["symptom_text"], "The input text should match the payload."
        assert "analysis" in json_data, "The response must contain an 'analysis' field."
        assert "model_response" in json_data, "The response must contain a 'model_response' field."

        print("Chatbot endpoint test passed with response:", json_data)