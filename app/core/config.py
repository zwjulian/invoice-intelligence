from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    gemini_api_key: str | None = None

    gemini_model: str = (
        "gemini-3.5-flash-lite"
    )

    use_mock_llm: bool = True

    database_url: str = (
        "sqlite:///./invoice_intelligence.db"
    )

    # Document-processing settings
    max_upload_size_mb: int = 10

    max_pdf_pages: int = 20

    # A PDF can technically contain embedded text while still
    # effectively being a scan. Only use text extraction when
    # there is enough meaningful text available.
    min_text_characters: int = 80

    vision_render_dpi: int = 150

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()