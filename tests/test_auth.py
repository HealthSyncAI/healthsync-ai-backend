import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.auth import get_current_user

# --- Dummy User Dependency for Authentication ---
class DummyUser:
    id = 1
    username = "dummy_user"

async def dummy_get_current_user():
    """Return a dummy user to bypass real authentication."""
    return DummyUser()

@pytest.mark.asyncio
async def test_registration_and_login():
    """
    Test the registration and login endpoints:
    - Successfully register a new user.
    - Reject duplicate registration.
    - Successfully log in with valid credentials.
    - Reject login attempts with invalid credentials.
    """
    # Override the get_current_user dependency to always return DummyUser.
    app.dependency_overrides[get_current_user] = dummy_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # -------------------- Test Registration --------------------
        register_payload = {
            "username": "testuser_auth",
            "email": "testuser_auth@example.com",
            "password": "SecretPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        reg_response = await client.post("/api/auth/register", json=register_payload)

        if reg_response.status_code != 201:
            print("Registration error details:", reg_response.json())

        assert reg_response.status_code == 201, f"Expected status 201, got {reg_response.status_code}"
        reg_data = reg_response.json()

        assert "access_token" in reg_data, "Registration should return an access_token"
        assert reg_data.get("token_type") == "bearer", "Token type should be 'bearer'"
        print("Registration successful for user: testuser_auth.")

        # -------------------- Test Duplicate Registration --------------------
        dup_response = await client.post("/api/auth/register", json=register_payload)
        assert dup_response.status_code == 400, f"Expected status 400 on duplicate registration, got {dup_response.status_code}"
        print("Duplicate registration correctly rejected.")

        # -------------------- Test Login with Valid Credentials --------------------
        valid_login_data = {
            "username": register_payload["username"],
            "password": register_payload["password"]
        }
        login_response = await client.post("/api/auth/login", data=valid_login_data)
        assert login_response.status_code == 200, f"Expected status 200 on login, got {login_response.status_code}"
        login_data = login_response.json()
        assert "access_token" in login_data, "Login should return an access_token"
        assert login_data.get("token_type") == "bearer", "Token type should be 'bearer'"
        print("Login successful with valid credentials.")

        # -------------------- Test Login with Invalid Credentials --------------------
        invalid_login_data = {
            "username": register_payload["username"],
            "password": "WrongPassword!"
        }
        inv_login_response = await client.post("/api/auth/login", data=invalid_login_data)
        assert inv_login_response.status_code == 400, f"Expected status 400 on invalid login, got {inv_login_response.status_code}"
        print("Login correctly rejected invalid credentials.")

    # Clean up dependency override.
    app.dependency_overrides.pop(get_current_user, None)