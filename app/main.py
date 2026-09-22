from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.models.invoice import Invoice
from app.services.llm_service import (
    GeminiInvoiceExtractor,
    InvoiceExtractionError,
)
from app.services.mock_llm_service import MockInvoiceExtractor
from app.services.pdf_service import (
    PDFExtractionError,
    extract_text_from_pdf,
    render_pdf_pages_as_png,
)
from app.services.validation_service import (
    ValidationResult,
    validate_invoice,
)

app = FastAPI(
    title="Invoice Intelligence API",
    description=(
        "Extract structured invoice data from PDF files "
        "using text or multimodal LLM processing."
    ),
    version="0.3.0",
)


FRONTEND_PATH = (
    Path(__file__).resolve().parent
    / "static"
    / "index.html"
)


class InvoiceAPIResponse(ValidationResult):
    filename: str
    extraction_method: str
    invoice: Invoice


if settings.use_mock_llm:
    extractor = MockInvoiceExtractor()
else:
    extractor = GeminiInvoiceExtractor()


@app.get(
    "/",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def frontend() -> HTMLResponse:
    html = FRONTEND_PATH.read_text(
        encoding="utf-8"
    )

    return HTMLResponse(
        content=html
    )


@app.get("/health")
def health_check() -> dict[str, str | bool]:
    return {
        "status": "healthy",
        "mock_llm": settings.use_mock_llm,
    }


@app.post(
    "/invoices/extract",
    response_model=InvoiceAPIResponse,
)
async def extract_invoice(
    file: Annotated[
        UploadFile,
        File(),
    ],
) -> InvoiceAPIResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    pdf_bytes = await file.read()

    temp_path: Path | None = None

    try:
        with NamedTemporaryFile(
            suffix=".pdf",
            delete=False,
        ) as temp_file:
            temp_file.write(
                pdf_bytes
            )

            temp_path = Path(
                temp_file.name
            )

        invoice_text = extract_text_from_pdf(
            temp_path
        )

        if invoice_text.strip():
            extraction_method = "text"

            invoice = extractor.extract(
                invoice_text
            )

        else:
            extraction_method = "vision"

            page_images = (
                render_pdf_pages_as_png(
                    temp_path
                )
            )

            invoice = (
                extractor.extract_from_images(
                    page_images
                )
            )

        validation = validate_invoice(
            invoice
        )

        return InvoiceAPIResponse(
            filename=(
                file.filename
                or "unknown.pdf"
            ),
            extraction_method=(
                extraction_method
            ),
            invoice=invoice,
            valid=validation.valid,
            warnings=validation.warnings,
        )

    except PDFExtractionError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except InvoiceExtractionError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    finally:
        if temp_path is not None:
            temp_path.unlink(
                missing_ok=True
            )