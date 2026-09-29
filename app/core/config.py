from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Gemini
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash-lite"
    use_mock_llm: bool = True

    # Database
    #
    # If DATABASE_URL is not configured, SQLite is used locally.
    # On Render we will use PostgreSQL via DATABASE_URL.
    database_url: str = "sqlite:///./invoice_intelligence.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()