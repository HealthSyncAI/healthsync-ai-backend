import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    PROJECT_NAME: str = "HealthSync AI"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ["true", "1", "yes"]
    # Add additional configuration items (like DB settings, OAuth2 secrets, etc.)

settings = Settings()