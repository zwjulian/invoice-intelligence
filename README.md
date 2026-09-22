\# Invoice Intelligence API



An LLM-powered document processing API that extracts structured invoice

information from PDF files and validates the extracted data using

deterministic business rules.



The project demonstrates a production-oriented approach to LLM application

development using Python, FastAPI, Pydantic, Gemini, automated testing and Docker.



\## Features



\- PDF text extraction using PyMuPDF

\- Structured invoice extraction using Google Gemini

\- Pydantic models for type-safe structured output

\- Deterministic business-rule validation

\- FastAPI REST API

\- Automatic Swagger / OpenAPI documentation

\- Mock LLM mode for deterministic development and testing

\- Automated tests using pytest

\- Docker support



\## Architecture



```text

PDF

&#x20;|

&#x20;v

FastAPI

&#x20;|

&#x20;v

PyMuPDF

&#x20;|

&#x20;| raw document text

&#x20;v

Gemini

&#x20;|

&#x20;| structured output

&#x20;v

Pydantic Invoice model

&#x20;|

&#x20;v

Business validation

&#x20;|

&#x20;v

JSON response

```



\## Extracted information



The current invoice schema extracts:



\- invoice number

\- invoice date

\- due date

\- supplier information

\- customer information

\- VAT numbers

\- currency

\- subtotal

\- VAT amount

\- total amount

\- invoice line items



Example:



```json

{

&#x20; "invoice\_number": "INV-2026-0042",

&#x20; "invoice\_date": "2026-09-15",

&#x20; "due\_date": "2026-10-15",

&#x20; "supplier": {

&#x20;   "name": "NorthStar Software B.V.",

&#x20;   "address": "Zernikepark 12, 9747 AN Groningen, Netherlands",

&#x20;   "vat\_number": "NL865432109B01"

&#x20; },

&#x20; "customer": {

&#x20;   "name": "Data Example B.V.",

&#x20;   "address": "Helperpark 100, 9723 ZA Groningen, Netherlands",

&#x20;   "vat\_number": "NL123456789B01"

&#x20; },

&#x20; "currency": "EUR",

&#x20; "subtotal": "1990.00",

&#x20; "vat\_amount": "417.90",

&#x20; "total\_amount": "2407.90"

}

```



\## Structured output



Instead of asking the LLM to return arbitrary JSON, the application defines

the expected invoice structure using Pydantic.



```text

Pydantic model

&#x20;     |

&#x20;     v

JSON schema

&#x20;     |

&#x20;     v

Gemini structured output

&#x20;     |

&#x20;     v

Validated Invoice object

```



This creates a clear contract between the LLM and the application.



\## Business validation



Valid structured output does not automatically mean that the extracted

invoice is logically correct.



The application therefore applies deterministic validation rules after the

LLM extraction.



Currently implemented checks include:



```text

subtotal + VAT ≈ total



sum(line item totals) ≈ subtotal



due date >= invoice date

```



A small monetary tolerance is allowed for rounding differences.



A successful validation returns:



```json

{

&#x20; "valid": true,

&#x20; "warnings": \[]

}

```



\## Mock LLM mode



External LLM services can experience latency, rate limits or temporary

availability problems.



For development and automated testing the project therefore supports a

deterministic mock extractor.



Enable it using:



```env

USE\_MOCK\_LLM=true

```



Production-style extraction can use Gemini with:



```env

USE\_MOCK\_LLM=false

```



\## Running locally



Requires Python 3.11.



Create a virtual environment:



```bash

python -m venv .venv

```



Install dependencies:



```bash

pip install -r requirements.txt

```



Create a `.env` file based on:



```text

.env.example

```



Start the API:



```bash

uvicorn app.main:app --reload

```



Then open:



```text

http://127.0.0.1:8000/docs

```



\## API



\### Health check



```http

GET /health

```



\### Extract invoice



```http

POST /invoices/extract

```



Upload a PDF using `multipart/form-data`.



The endpoint returns the extracted invoice together with the validation result.



\## Tests



Run:



```bash

pytest -v

```



Current test suite:



```text

8 passed

```



The tests cover:



\- valid invoices

\- incorrect invoice totals

\- incorrect subtotals

\- invalid due dates

\- monetary rounding tolerance

\- API health endpoint

\- invoice upload endpoint

\- invalid file types



Mock mode is used during automated tests so the test suite does not depend

on an external LLM service.



\## Docker



Build the image:



```bash

docker build -t invoice-intelligence .

```



Run:



```bash

docker run --env-file .env -p 8000:8000 invoice-intelligence

```



Then visit:



```text

http://127.0.0.1:8000/docs

```



\## Limitations



The current PDF extraction works best with digitally generated PDFs that

contain embedded text.



Scanned invoices may require OCR or a multimodal vision model.



External LLM availability and latency can vary. Mock mode is therefore used

for deterministic development and testing.



\## Possible future improvements



\- OCR / multimodal support for scanned invoices

\- field-level LLM evaluation

\- PostgreSQL persistence

\- extraction confidence scores

\- CI/CD

\- frontend

\- support for multiple document types

\- RAG over collections of processed invoices

