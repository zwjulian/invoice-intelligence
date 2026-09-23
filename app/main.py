from pathlib import Path
from typing import Annotated

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.document_config import document_settings
from app.models.analytics import AnalyticsSummary
from app.models.invoice import Invoice
from app.models.stored_invoice import (
    InvoiceStatusUpdate,
    StoredInvoiceDetail,
    StoredInvoiceSummary,
)
from app.services.document_processing_service import (
    DocumentTooLargeError,
    DocumentTooManyPagesError,
    InvalidDocumentError,
    process_invoice_pdf,
)
from app.services.llm_service import (
    GeminiInvoiceExtractor,
    InvoiceExtractionError,
)
from app.services.mock_llm_service import (
    MockInvoiceExtractor,
)
from app.services.pdf_service import (
    PDFExtractionError,
)
from app.services.storage_service import (
    get_analytics_summary,
    get_stored_invoice,
    list_stored_invoices,
    store_invoice,
    update_invoice_status,
)
from app.services.validation_service import (
    ValidationResult,
    validate_invoice,
)

app = FastAPI(
    title="Invoice Intelligence API",
    description=(
        "API for extracting, validating, storing, "
        "managing and analysing invoice information."
    ),
)


STATIC_PATH = (
    Path(__file__).resolve().parent
    / "static"
)


app.mount(
    "/static",
    StaticFiles(
        directory=STATIC_PATH
    ),
    name="static",
)


class InvoiceAPIResponse(
    ValidationResult
):
    filename: str

    extraction_method: str

    extracted_text_characters: int

    page_count: int

    invoice: Invoice

    database_id: int

    duplicate: bool

    duplicate_of_id: int | None


if settings.use_mock_llm:
    extractor = MockInvoiceExtractor()
else:
    extractor = GeminiInvoiceExtractor()


def read_html(
    filename: str,
) -> HTMLResponse:
    path = (
        STATIC_PATH
        / filename
    )

    html = path.read_text(
        encoding="utf-8"
    )

    return HTMLResponse(
        content=html
    )


@app.get(
    "/",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def dashboard() -> HTMLResponse:
    return read_html(
        "index.html"
    )


@app.get(
    "/invoices",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def invoice_page() -> HTMLResponse:
    return read_html(
        "invoices.html"
    )


@app.get(
    "/invoices/{invoice_id}",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def invoice_detail_page(
    invoice_id: int,
) -> HTMLResponse:
    return read_html(
        "invoice_detail.html"
    )


@app.get(
    "/analytics",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def analytics_page() -> HTMLResponse:
    return read_html(
        "analytics.html"
    )


@app.get(
    "/api/health"
)
def health_check() -> dict[
    str,
    str | bool | int,
]:
    return {
        "status": "healthy",
        "mock_llm": settings.use_mock_llm,
        "max_upload_size_mb": (
            document_settings.max_upload_size_mb
        ),
        "max_pdf_pages": (
            document_settings.max_pdf_pages
        ),
    }


@app.get(
    "/api/analytics/summary",
    response_model=AnalyticsSummary,
)
def analytics_summary() -> AnalyticsSummary:
    return get_analytics_summary()


@app.get(
    "/api/invoices",
    response_model=list[
        StoredInvoiceSummary
    ],
)
def invoices(
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=500,
        ),
    ] = 100,
) -> list[
    StoredInvoiceSummary
]:
    stored_invoices = (
        list_stored_invoices(
            limit=limit
        )
    )

    return [
        StoredInvoiceSummary.model_validate(
            invoice
        )
        for invoice
        in stored_invoices
    ]


@app.get(
    "/api/invoices/{invoice_id}",
    response_model=StoredInvoiceDetail,
)
def invoice_detail(
    invoice_id: int,
) -> StoredInvoiceDetail:
    stored_invoice = (
        get_stored_invoice(
            invoice_id
        )
    )

    if stored_invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found.",
        )

    return StoredInvoiceDetail.model_validate(
        stored_invoice
    )


@app.patch(
    "/api/invoices/{invoice_id}/status",
    response_model=StoredInvoiceSummary,
)
def change_invoice_status(
    invoice_id: int,
    update: InvoiceStatusUpdate,
) -> StoredInvoiceSummary:
    stored_invoice = get_stored_invoice(
        invoice_id
    )

    if stored_invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found.",
        )

    current_status = stored_invoice.status
    requested_status = update.status

    allowed_transitions = {
        "new": {
            "approved",
        },
        "approved": {
            "new",
            "paid",
        },
        "paid": {
            "approved",
        },
    }

    if (
        requested_status
        != current_status
        and requested_status
        not in allowed_transitions.get(
            current_status,
            set(),
        )
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid status transition "
                f"from '{current_status}' "
                f"to '{requested_status}'."
            ),
        )

    updated_invoice = update_invoice_status(
        invoice_id=invoice_id,
        status=requested_status,
    )

    if updated_invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found.",
        )

    return StoredInvoiceSummary.model_validate(
        updated_invoice
    )


@app.post(
    "/api/invoices/extract",
    response_model=InvoiceAPIResponse,
)
async def extract_invoice(
    file: Annotated[
        UploadFile,
        File(),
    ],
) -> InvoiceAPIResponse:
    filename = (
        file.filename
        or "upload.pdf"
    )

    if (
        Path(filename).suffix.lower()
        != ".pdf"
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Only PDF files are supported."
            ),
        )

    # Read at most one byte beyond the limit. That allows us to
    # reject oversized uploads without loading an arbitrarily
    # large file completely into memory.
    max_size_bytes = (
        document_settings.max_upload_size_mb
        * 1024
        * 1024
    )

    pdf_bytes = await file.read(
        max_size_bytes + 1
    )

    if len(pdf_bytes) > max_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=(
                "Uploaded PDF exceeds the maximum "
                f"size of "
                f"{document_settings.max_upload_size_mb} MB."
            ),
        )

    try:
        processing_result = process_invoice_pdf(
            pdf_bytes=pdf_bytes,
            extractor=extractor,
        )

        invoice = processing_result.invoice

        validation = validate_invoice(
            invoice
        )

        stored_invoice = store_invoice(
            filename=filename,
            extraction_method=(
                processing_result.extraction_method
            ),
            invoice=invoice,
            validation=validation,
        )

        duplicate = (
            stored_invoice.duplicate_of_id
            is not None
        )

        return InvoiceAPIResponse(
            filename=filename,
            extraction_method=(
                processing_result.extraction_method
            ),
            extracted_text_characters=(
                processing_result
                .extracted_text_characters
            ),
            page_count=(
                processing_result.page_count
            ),
            invoice=invoice,
            valid=validation.valid,
            warnings=validation.warnings,
            database_id=stored_invoice.id,
            duplicate=duplicate,
            duplicate_of_id=(
                stored_invoice.duplicate_of_id
            ),
        )

    except InvalidDocumentError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except DocumentTooLargeError as exc:
        raise HTTPException(
            status_code=413,
            detail=str(exc),
        ) from exc

    except DocumentTooManyPagesError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

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