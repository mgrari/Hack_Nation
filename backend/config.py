from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    openai_api_key: str
    fernet_key: str
    consent_version: str = "2026-07-18"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
