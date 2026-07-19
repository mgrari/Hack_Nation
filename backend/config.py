from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    openai_api_key: str
    fernet_key: str
    consent_version: str = "2026-07-18"
    frontend_origin: str = "http://localhost:3000"
    environment: str = "development"
    # How long a renter's session (and thus their uploaded documents) persists on their
    # device, so they can close the browser and return later to add another document.
    # Bounded on purpose -- retention is minimal and the renter can always delete sooner.
    session_ttl_days: int = 30

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
