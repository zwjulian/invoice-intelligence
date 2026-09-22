from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated

from fastapi import (
    FastAPI,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.database import init_db
from app.models.invoice import Invoice
from app.models.stored_invoice import (
    InvoiceStatusUpdate,
    StoredInvoiceDetail,
    StoredInvoiceSummary,
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
    extract_text_from_pdf,
    render_pdf_pages_as_png,
)
from app.services.storage_service import (
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
        "Extract, validate, store and manage "
        "structured invoice information."
    ),
    version="0.5.0",
)


FRONTEND_PATH = (
    Path(__file__).resolve().parent
    / "static"
    / "index.html"
)


class InvoiceAPIResponse(
    ValidationResult
):
    filename: str

    extraction_method: str

    invoice: Invoice

    database_id: int

    duplicate: bool

    duplicate_of_id: int | None


if settings.use_mock_llm:
    extractor = (
        MockInvoiceExtractor()
    )
else:
    extractor = (
        GeminiInvoiceExtractor()
    )


init_db()


@app.get(
    "/",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def frontend() -> HTMLResponse:
    html = (
        FRONTEND_PATH.read_text(
            encoding="utf-8"
        )
    )

    return HTMLResponse(
        content=html
    )


@app.get("/health")
def health_check() -> dict[
    str,
    str | bool,
]:
    return {
        "status": "healthy",
        "mock_llm": (
            settings.use_mock_llm
        ),
    }


@app.get(
    "/invoices",
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
        StoredInvoiceSummary
        .model_validate(
            invoice
        )
        for invoice
        in stored_invoices
    ]


@app.get(
    "/invoices/{invoice_id}",
    response_model=(
        StoredInvoiceDetail
    ),
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
            detail=(
                "Invoice not found."
            ),
        )

    return (
        StoredInvoiceDetail
        .model_validate(
            stored_invoice
        )
    )


@app.patch(
    "/invoices/{invoice_id}/status",
    response_model=(
        StoredInvoiceSummary
    ),
)
def change_invoice_status(
    invoice_id: int,
    update: InvoiceStatusUpdate,
) -> StoredInvoiceSummary:
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

    current_status = (
        stored_invoice.status
    )

    requested_status = (
        update.status
    )

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

    updated_invoice = (
        update_invoice_status(
            invoice_id=invoice_id,
            status=requested_status,
        )
    )

    if updated_invoice is None:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found.",
        )

    return (
        StoredInvoiceSummary
        .model_validate(
            updated_invoice
        )
    )


@app.post(
    "/invoices/extract",
    response_model=(
        InvoiceAPIResponse
    ),
)
async def extract_invoice(
    file: Annotated[
        UploadFile,
        File(),
    ],
) -> InvoiceAPIResponse:
    if (
        file.content_type
        != "application/pdf"
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Only PDF files "
                "are supported."
            ),
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

        invoice_text = (
            extract_text_from_pdf(
                temp_path
            )
        )

        if invoice_text.strip():
            extraction_method = (
                "text"
            )

            invoice = (
                extractor.extract(
                    invoice_text
                )
            )

        else:
            extraction_method = (
                "vision"
            )

            page_images = (
                render_pdf_pages_as_png(
                    temp_path
                )
            )

            invoice = (
                extractor
                .extract_from_images(
                    page_images
                )
            )

        validation = (
            validate_invoice(
                invoice
            )
        )

        filename = (
            file.filename
            or "unknown.pdf"
        )

        stored_invoice = (
            store_invoice(
                filename=filename,
                extraction_method=(
                    extraction_method
                ),
                invoice=invoice,
                validation=validation,
            )
        )

        duplicate = (
            stored_invoice
            .duplicate_of_id
            is not None
        )

        return InvoiceAPIResponse(
            filename=filename,
            extraction_method=(
                extraction_method
            ),
            invoice=invoice,
            valid=validation.valid,
            warnings=(
                validation.warnings
            ),
            database_id=(
                stored_invoice.id
            ),
            duplicate=duplicate,
            duplicate_of_id=(
                stored_invoice
                .duplicate_of_id
            ),
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