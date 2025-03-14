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
    open_router_api_key: str = Field(..., alias="OPEN_ROUTER_API_KEY")

    # Mailjet settings
    MAILJET_API_KEY: str = Field(..., alias="MAILJET_API_KEY")
    MAILJET_SECRET_KEY: str = Field(..., alias="MAILJET_SECRET_KEY")
    MAILJET_FROM_EMAIL: str = Field(..., alias="MAILJET_FROM_EMAIL")
    MAILJET_FROM_NAME: str = Field("HealthSync AI", alias="MAILJET_FROM_NAME")


settings = Settings()
