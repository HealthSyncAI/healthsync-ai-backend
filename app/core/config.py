from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

    database_uri: str = Field(..., alias="DATABASE_URI")
    secret_key: str = Field(..., alias="SECRET_KEY")
    api_endpoint: str = Field(..., alias="API_ENDPOINT")
    debug: bool = Field(False, alias="DEBUG")


settings = Settings()
