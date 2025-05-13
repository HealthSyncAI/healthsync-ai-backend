from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_uri: str = Field(..., alias="DATABASE_URI")
    database_test_uri: str = Field(..., alias="DATABASE_TEST_URI")

    secret_key: str = Field(..., alias="SECRET_KEY")
    api_endpoint: str = Field(..., alias="API_ENDPOINT")
    debug: bool = Field(False, alias="DEBUG")

    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    requesty_api_key: str = Field(..., alias="REQUESTY_API_KEY")
    requesty_router_base_url: str = "https://router.requesty.ai/v1"
    requesty_model_name: str = "google/gemini-2.0-flash-exp" # As requested
    requesty_max_output_tokens: int = 2048

    SMTP_SERVER: str = Field(..., alias="SMTP_SERVER")
    SMTP_PORT: int = Field(587, alias="SMTP_PORT")
    SMTP_USERNAME: str = Field(..., alias="SMTP_USERNAME")
    SMTP_PASSWORD: str = Field(..., alias="SMTP_PASSWORD")
    SMTP_FROM_EMAIL: str = Field(..., alias="SMTP_FROM_EMAIL")
    SMTP_FROM_NAME: str = Field("HealthSync AI", alias="SMTP_FROM_NAME")


settings = Settings()