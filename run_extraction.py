from app.services.llm_service import GeminiInvoiceExtractor
from app.services.pdf_service import extract_text_from_pdf
from app.services.validation_service import validate_invoice


def main() -> None:
    pdf_path = "sample_data/test_invoice.pdf"

    print("1. Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)

    print("2. Sending document to Gemini...")
    extractor = GeminiInvoiceExtractor()

    invoice = extractor.extract(text)

    print("\n3. Structured result:")
    print("=" * 60)

    print(
        invoice.model_dump_json(
            indent=2
        )
    )

    print("\n4. Validating invoice...")
    print("=" * 60)

    validation = validate_invoice(invoice)

    print(
        validation.model_dump_json(
            indent=2
        )
    )


if __name__ == "__main__":
    main()