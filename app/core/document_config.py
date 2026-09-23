from pydantic_settings import BaseSettings, SettingsConfigDict


class DocumentSettings(BaseSettings):
    """
    Configuration for uploaded invoice documents.

    These settings are intentionally kept separate from the LLM
    configuration so document-processing behaviour can be changed
    without touching model configuration.
    """

    max_upload_size_mb: int = 10

    max_pdf_pages: int = 20

    # Some scanned PDFs contain a tiny amount of embedded text,
    # such as "Page 1". We only use text extraction when the PDF
    # contains a meaningful amount of text.
    min_text_characters: int = 80

    # Resolution used when PDF pages are rendered for Gemini Vision.
    vision_render_dpi: int = 150

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


document_settings = DocumentSettings()