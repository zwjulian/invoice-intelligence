\# Invoice Intelligence API



An LLM-powered document processing API that extracts structured invoice

information from PDF files and validates the extracted data using

deterministic business rules.



The project demonstrates a production-oriented approach to LLM application

development using Python, FastAPI, Pydantic, Google Gemini, automated testing,

Docker and continuous integration.



\---



\## Features



\- PDF text extraction using PyMuPDF

\- Structured invoice extraction using Google Gemini

\- Pydantic models for type-safe structured output

\- Deterministic business-rule validation

\- FastAPI REST API

\- Automatic OpenAPI / Swagger documentation

\- Mock LLM mode for deterministic development and testing

\- Automated unit and API tests using pytest

\- Docker containerization

\- GitHub Actions continuous integration

\- Field-level LLM evaluation against a golden dataset



\---



\## Architecture



```text

&#x20;                        PDF

&#x20;                         |

&#x20;                         v

&#x20;                 +---------------+

&#x20;                 |    FastAPI    |

&#x20;                 +-------+-------+

&#x20;                         |

&#x20;                         v

&#x20;                 +---------------+

&#x20;                 |    PyMuPDF    |

&#x20;                 | PDF extraction|

&#x20;                 +-------+-------+

&#x20;                         |

&#x20;                      raw text

&#x20;                         |

&#x20;                         v

&#x20;                 +---------------+

&#x20;                 |    Gemini     |

&#x20;                 |  structured   |

&#x20;                 |  extraction   |

&#x20;                 +-------+-------+

&#x20;                         |

&#x20;                         v

&#x20;                 +---------------+

&#x20;                 |   Pydantic    |

&#x20;                 | Invoice model |

&#x20;                 +-------+-------+

&#x20;                         |

&#x20;                         v

&#x20;                 +---------------+

&#x20;                 |   Business    |

&#x20;                 |  validation   |

&#x20;                 +-------+-------+

&#x20;                         |

&#x20;                         v

&#x20;                   JSON response

```



The LLM is responsible for extracting information from unstructured document

text, while deterministic Python code is used to validate the resulting data.



\---



\## Extracted information



The current invoice schema extracts:



\- invoice number

\- invoice date

\- payment due date

\- supplier name

\- supplier address

\- supplier VAT number

\- customer name

\- customer address

\- customer VAT number

\- currency

\- subtotal

\- VAT amount

\- total amount

\- individual invoice line items

\- quantities

\- unit prices

\- VAT rates

\- line totals



Example output:



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

&#x20; "total\_amount": "2407.90",

&#x20; "line\_items": \[

&#x20;   {

&#x20;     "description": "AI consultancy - architecture workshop",

&#x20;     "quantity": "2",

&#x20;     "unit\_price": "450.00",

&#x20;     "vat\_rate": "21",

&#x20;     "total": "900.00"

&#x20;   }

&#x20; ]

}

```



\---



\## Structured output



A normal LLM prompt can return inconsistent JSON or unexpected field names.



This project instead defines the expected output using a Pydantic `Invoice`

model.



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



This creates a clear contract between the LLM and the rest of the application.



For example, fields such as invoice dates are parsed as Python dates and

monetary values are represented using `Decimal`.



\---



\## Business validation



Valid structured output does not automatically mean that the extracted

invoice is logically correct.



The application therefore applies deterministic business rules after the LLM

extraction.



Current checks include:



```text

subtotal + VAT ≈ total amount



sum(line item totals) ≈ subtotal



due date >= invoice date

```



A small monetary tolerance is allowed to handle minor rounding differences.



A valid invoice produces:



```json

{

&#x20; "valid": true,

&#x20; "warnings": \[]

}

```



An inconsistent invoice could produce:



```json

{

&#x20; "valid": false,

&#x20; "warnings": \[

&#x20;   "Subtotal plus VAT does not match total amount."

&#x20; ]

}

```



This separates two different concerns:



```text

Pydantic validation

→ Is the structure and datatype correct?



Business validation

→ Does the extracted invoice logically make sense?

```



\---



\## Mock LLM mode



External LLM services can experience latency, rate limits or temporary

availability issues.



The project therefore provides two extraction modes.



\### Gemini mode



```text

PDF

→ PyMuPDF

→ Gemini

→ Pydantic Invoice

→ business validation

```



\### Mock mode



```text

PDF

→ PyMuPDF

→ deterministic MockInvoiceExtractor

→ business validation

```



Mock mode can be enabled using:



```env

USE\_MOCK\_LLM=true

```



The real Gemini extractor can be enabled using:



```env

USE\_MOCK\_LLM=false

```



Using a deterministic mock makes automated tests independent of external LLM

availability, latency and API limits.



\---



\## Installation



The project uses Python 3.11.



Clone the repository:



```bash

git clone https://github.com/YOUR\_USERNAME/invoice-intelligence.git

cd invoice-intelligence

```



Create a virtual environment:



```bash

python -m venv .venv

```



Activate it on Windows PowerShell:



```powershell

.\\.venv\\Scripts\\Activate.ps1

```



Install dependencies:



```bash

pip install -r requirements.txt

```



\---



\## Environment configuration



Create a `.env` file based on `.env.example`.



Example:



```env

GEMINI\_API\_KEY=your\_api\_key\_here

GEMINI\_MODEL=gemini-3.5-flash-lite

USE\_MOCK\_LLM=true

```



The real `.env` file is ignored by Git and should never be committed.



\---



\## Running the API locally



Start FastAPI using Uvicorn:



```bash

uvicorn app.main:app --reload

```



Open:



```text

http://127.0.0.1:8000/docs

```



FastAPI automatically provides an interactive Swagger interface.



A PDF invoice can be uploaded directly from this page.



\---



\## API endpoints



\### Health check



```http

GET /health

```



Example response:



```json

{

&#x20; "status": "healthy",

&#x20; "mock\_llm": true

}

```



\### Extract invoice



```http

POST /invoices/extract

```



The request accepts an invoice PDF using `multipart/form-data`.



Example response:



```json

{

&#x20; "valid": true,

&#x20; "warnings": \[],

&#x20; "filename": "test\_invoice.pdf",

&#x20; "invoice": {

&#x20;   "invoice\_number": "INV-2026-0042",

&#x20;   "invoice\_date": "2026-09-15",

&#x20;   "due\_date": "2026-10-15",

&#x20;   "currency": "EUR",

&#x20;   "subtotal": "1990.00",

&#x20;   "vat\_amount": "417.90",

&#x20;   "total\_amount": "2407.90"

&#x20; }

}

```



Non-PDF files are rejected by the API.



\---



\## Automated tests



Tests are implemented using `pytest`.



Run:



```bash

pytest -v

```



Current result:



```text

8 passed

```



The test suite currently covers:



\- successful invoice validation

\- incorrect invoice totals

\- incorrect subtotals

\- invalid due dates

\- monetary rounding tolerance

\- API health endpoint

\- successful invoice PDF upload

\- rejection of unsupported file types



The tests use mock mode, which means they do not depend on Gemini.



This keeps them:



\- deterministic

\- fast

\- free to run

\- independent of external API availability



\---



\## Continuous integration



GitHub Actions automatically runs the test suite after pushes and pull

requests to the `main` branch.



The CI pipeline performs:



```text

Checkout repository

&#x20;       |

&#x20;       v

Install Python 3.11

&#x20;       |

&#x20;       v

Install dependencies

&#x20;       |

&#x20;       v

Run pytest

&#x20;       |

&#x20;       v

Build Docker image

```



This ensures that both the Python application and Docker build remain valid

after code changes.



\---



\## Docker



The application can also run completely inside a Docker container.



Build the image:



```bash

docker build -t invoice-intelligence .

```



Run:



```bash

docker run --env-file .env -p 8000:8000 invoice-intelligence

```



Then open:



```text

http://127.0.0.1:8000/docs

```



The same FastAPI application is now running inside the Docker container.



Docker makes the application easier to reproduce across different

environments because the Python runtime and dependencies are packaged with

the application.



\---



\## LLM Evaluation



The real Gemini extraction pipeline is evaluated separately from the

deterministic unit and API tests.



A small synthetic golden dataset currently contains \*\*5 invoices\*\* with known

ground-truth values.



Each generated invoice has a matching JSON ground-truth file.



```text

evaluation/

├── invoices/

│   ├── invoice\_001.pdf

│   ├── invoice\_002.pdf

│   ├── invoice\_003.pdf

│   ├── invoice\_004.pdf

│   └── invoice\_005.pdf

│

├── ground\_truth/

│   ├── invoice\_001.json

│   ├── invoice\_002.json

│   ├── invoice\_003.json

│   ├── invoice\_004.json

│   └── invoice\_005.json

│

├── evaluate.py

└── results.json

```



The evaluation pipeline performs:



```text

Known invoice PDF

&#x20;      |

&#x20;      v

PDF text extraction

&#x20;      |

&#x20;      v

Real Gemini extraction

&#x20;      |

&#x20;      v

Predicted Invoice

&#x20;      |

&#x20;      v

Compare with ground truth

&#x20;      |

&#x20;      v

Field-level accuracy

```



The current evaluation compares 11 fields per invoice.



\### Current results



| Field | Correct | Accuracy |

|---|---:|---:|

| Invoice number | 5/5 | 100% |

| Invoice date | 5/5 | 100% |

| Due date | 5/5 | 100% |

| Currency | 5/5 | 100% |

| Subtotal | 5/5 | 100% |

| VAT amount | 5/5 | 100% |

| Total amount | 5/5 | 100% |

| Supplier name | 5/5 | 100% |

| Supplier VAT number | 5/5 | 100% |

| Customer name | 5/5 | 100% |

| Customer VAT number | 5/5 | 100% |



\*\*Overall result: 55/55 evaluated fields correct (100%).\*\*



The benchmark can be reproduced using:



```bash

python -m evaluation.evaluate

```



Detailed results are written to:



```text

evaluation/results.json

```



The evaluation uses the real Gemini extractor and is therefore intentionally

kept separate from the deterministic CI test suite.



\### Interpreting the result



The current 100% score should be interpreted as a \*\*sanity-check benchmark\*\*,

not as a claim that the system achieves 100% accuracy on arbitrary real-world

invoices.



The current evaluation dataset is:



\- small

\- synthetic

\- relatively clean

\- limited in layout variation



A larger and more diverse benchmark would be required to estimate real-world

performance.



\---



\## Project structure



```text

invoice-intelligence/

│

├── app/

│   ├── core/

│   │   └── config.py

│   │

│   ├── models/

│   │   └── invoice.py

│   │

│   ├── services/

│   │   ├── llm\_service.py

│   │   ├── mock\_llm\_service.py

│   │   ├── pdf\_service.py

│   │   └── validation\_service.py

│   │

│   └── main.py

│

├── evaluation/

│   ├── ground\_truth/

│   ├── invoices/

│   ├── evaluate.py

│   └── results.json

│

├── scripts/

│   └── generate\_evaluation\_data.py

│

├── sample\_data/

│   └── test\_invoice.pdf

│

├── tests/

│   ├── test\_api.py

│   └── test\_validation.py

│

├── .github/

│   └── workflows/

│       └── tests.yml

│

├── .dockerignore

├── .env.example

├── .gitignore

├── Dockerfile

├── README.md

├── requirements.txt

└── run\_extraction.py

```



\---



\## Limitations



The current PDF extraction approach works best for digitally generated PDF

files that contain embedded text.



Scanned documents may not contain machine-readable text and may therefore

require:



\- OCR

\- multimodal document understanding

\- vision-language models



The current evaluation dataset is also still small and synthetic.



External LLM availability can vary. The Gemini API may experience latency,

rate limits or temporary service availability issues.



For this reason, deterministic mock mode is used during development and CI.



\---



\## Possible future improvements



\### Document processing



\- OCR fallback for scanned invoices

\- multimodal PDF processing

\- support for image-based invoices

\- improved handling of complex PDF layouts



\### Evaluation



\- larger golden dataset

\- more realistic invoice layouts

\- missing-field test cases

\- multiple currencies

\- line-item-level evaluation

\- intentionally noisy PDF extraction

\- field precision / recall metrics



\### Application



\- PostgreSQL persistence

\- invoice search

\- batch processing

\- frontend interface

\- authentication

\- background processing



\### LLM engineering



\- extraction confidence scores

\- model comparison

\- prompt versioning

\- fallback LLM providers

\- observability and tracing

\- cost and latency monitoring



\### Retrieval



A future version could store processed invoices and support semantic

questions across a collection of documents using retrieval-augmented

generation (RAG).



Structured questions such as exact totals would remain suitable for SQL,

while semantic document questions could use vector search.



\---



\## Main technologies



\- Python 3.11

\- FastAPI

\- Pydantic

\- Google Gemini

\- PyMuPDF

\- pytest

\- Docker

\- GitHub Actions



\---



\## Goal of the project



The goal of this project is not only to demonstrate an LLM call.



It explores how an LLM can be integrated into a more complete software

system:



```text

unstructured document

&#x20;       |

&#x20;       v

LLM extraction

&#x20;       |

&#x20;       v

typed structured data

&#x20;       |

&#x20;       v

deterministic validation

&#x20;       |

&#x20;       v

REST API

&#x20;       |

&#x20;       v

automated testing

&#x20;       |

&#x20;       v

Docker

&#x20;       |

&#x20;       v

CI

&#x20;       |

&#x20;       v

quantitative LLM evaluation

```



The focus is therefore on combining AI functionality with software

engineering, reliability and evaluation.

