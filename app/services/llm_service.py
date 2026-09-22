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

    @staticmethod
    def extraction_prompt() -> str:
        return """
You are an invoice information extraction system.

Extract the invoice information from the provided document.

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
- Extract every invoice line item when possible.
- Line item totals should represent amounts excluding VAT when that is clear.
- If the invoice contains a VAT breakdown, extract each VAT rate separately.
- For each VAT breakdown entry:
  - rate is the VAT percentage.
  - taxable_amount is the amount excluding VAT to which that rate applies.
  - vat_amount is the VAT charged for that rate.
- If multiple VAT rates are shown, preserve them as separate entries.
- Do not combine different VAT rates.
"""

    def extract(
        self,
        invoice_text: str,
    ) -> Invoice:
        prompt = (
            self.extraction_prompt()
            + "\n\nInvoice text:\n\n"
            + invoice_text
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Invoice,
                ),
            )

            return self._parse_response(
                response
            )

        except InvoiceExtractionError:
            raise

        except Exception as exc:
            raise InvoiceExtractionError(
                f"Invoice extraction failed: {exc}"
            ) from exc

    def extract_from_images(
        self,
        page_images: list[bytes],
    ) -> Invoice:
        contents: list = []

        contents.append(
            self.extraction_prompt()
        )

        for index, image_bytes in enumerate(
            page_images,
            start=1,
        ):
            contents.append(
                f"Invoice page {index}:"
            )

            contents.append(
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/png",
                )
            )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Invoice,
                ),
            )

            return self._parse_response(
                response
            )

        except InvoiceExtractionError:
            raise

        except Exception as exc:
            raise InvoiceExtractionError(
                "Image-based invoice extraction "
                f"failed: {exc}"
            ) from exc

    @staticmethod
    def _parse_response(
        response,
    ) -> Invoice:
        if response.parsed is not None:
            return response.parsed

        if response.text is None:
            raise InvoiceExtractionError(
                "Gemini returned no structured response."
            )

        return Invoice.model_validate_json(
            response.text
        )