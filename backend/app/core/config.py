from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Configuration loaded exclusively from environment variables."""
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.6-terra"
    planner_model: str | None = None
    designer_model: str | None = None
    assessment_model: str | None = None
    reviewer_model: str | None = None
    frontend_origin: str = "http://localhost:5173"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
