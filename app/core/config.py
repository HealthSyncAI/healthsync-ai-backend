from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    # Database URI e.g., "postgresql://user:password@localhost/dbname"
    database_uri: str = Field(..., env="DATABASE_URI")

    # Secret key for JWT token signing or other security purposes
    secret_key: str = Field(..., env="SECRET_KEY")

    # External API endpoint to connect with third-party services
    api_endpoint: str = Field(..., env="API_ENDPOINT")

    # Flag to enable/disable debug mode
    debug: bool = Field(False, env="DEBUG")

    class Config:
        # Loads environment variables from a file named ".env"
        env_file = ".env"
        env_file_encoding = "utf-8"


# Instantiate the settings so they can be used throughout your project.
settings = Settings()
