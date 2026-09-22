from google import genai
from google.genai import types

from app.core.config import settings
from app.models.invoice import Invoice


class InvoiceExtractionError(Exception):
    """Raised when invoice extraction fails."""


class GeminiInvoiceExtractor:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise InvoiceExtractionError(
                "GEMINI_API_KEY is required when using Gemini."
            )

        self.client = genai.Client(
            api_key=settings.gemini_api_key
        )

        self.model = settings.gemini_model

    def extract(self, invoice_text: str) -> Invoice:
        prompt = f"""
You are an invoice information extraction system.

Extract the invoice information from the text below.

Rules:
- Only extract information supported by the document.
- Do not invent missing information.
- Use null when optional information is unavailable.
- Dates must use YYYY-MM-DD format.
- Currency must use ISO codes such as EUR, USD or GBP.
- Monetary fields must contain only numeric values.
- VAT rate 21% should be represented as 21.
- Distinguish carefully between supplier and customer.
- Ignore bank account details because they are not part of the requested schema.
- PDF text extraction can cause neighbouring text to become concatenated.
- Infer values only when the intended value is clear from context.
- Extract every invoice line item when possible.
- Line item totals should represent amounts excluding VAT when that is clear.
- If the invoice contains a VAT breakdown, extract each VAT rate separately.
- For each VAT breakdown entry:
  - rate is the VAT percentage.
  - taxable_amount is the amount excluding VAT to which that rate applies.
  - vat_amount is the VAT charged for that rate.
- If multiple VAT rates such as 9% and 21% are shown, preserve them as
  separate VAT breakdown entries.
- Do not combine different VAT rates into one VAT breakdown entry.

Invoice text:

{invoice_text}
"""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Invoice,
                ),
            )

            if response.parsed is not None:
                return response.parsed

            if response.text is None:
                raise InvoiceExtractionError(
                    "Gemini returned no text or parsed response."
                )

            return Invoice.model_validate_json(
                response.text
            )

        except InvoiceExtractionError:
            raise

        except Exception as exc:
            raise InvoiceExtractionError(
                f"Invoice extraction failed: {exc}"
            ) from exc