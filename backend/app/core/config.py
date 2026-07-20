from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Configuration loaded exclusively from environment variables."""
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.6-terra"
    planner_model: str | None = None
    designer_model: str | None = None
    assessment_model: str | None = None
    materials_model: str | None = None
    reviewer_model: str | None = None
    mock_mode: bool = Field(default=False, validation_alias="CLARA_MOCK_MODE")
    frontend_origin: str = "http://localhost:5173"
    coverage_db_path: str = "data/clara_coverage.sqlite3"
    # Student section. No fallback identity is allowed: endpoints stay disabled
    # until a real Supabase project and server-only service key are configured.
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_jwt_issuer: str | None = None
    supabase_jwt_audience: str = "authenticated"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
