import json
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent

INVOICE_DIR = ROOT / "evaluation" / "invoices"
GROUND_TRUTH_DIR = (
    ROOT / "evaluation" / "ground_truth"
)

INVOICE_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

GROUND_TRUTH_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


INVOICES = [
    {
        "id": "invoice_001",
        "invoice_number": "INV-2026-1001",
        "invoice_date": "2026-09-01",
        "due_date": "2026-10-01",
        "supplier": {
            "name": "NorthStar Software B.V.",
            "address": (
                "Zernikepark 12, "
                "9747 AN Groningen, Netherlands"
            ),
            "vat_number": "NL865432109B01",
        },
        "customer": {
            "name": "Data Example B.V.",
            "address": (
                "Helperpark 100, "
                "9723 ZA Groningen, Netherlands"
            ),
            "vat_number": "NL123456789B01",
        },
        "currency": "EUR",
        "subtotal": "1000.00",
        "vat_amount": "210.00",
        "total_amount": "1210.00",
        "line_items": [
            {
                "description": "AI consultancy",
                "quantity": "5",
                "unit_price": "200.00",
                "vat_rate": "21",
                "total": "1000.00",
            }
        ],
    },

    {
        "id": "invoice_002",
        "invoice_number": "2026-ACME-88",
        "invoice_date": "2026-08-20",
        "due_date": "2026-09-19",
        "supplier": {
            "name": "Acme Analytics B.V.",
            "address": (
                "Stationsweg 14, "
                "8011 CZ Zwolle, Netherlands"
            ),
            "vat_number": "NL111222333B01",
        },
        "customer": {
            "name": "Example Retail B.V.",
            "address": (
                "Marktstraat 8, "
                "9712 AB Groningen, Netherlands"
            ),
            "vat_number": "NL444555666B01",
        },
        "currency": "EUR",
        "subtotal": "750.00",
        "vat_amount": "157.50",
        "total_amount": "907.50",
        "line_items": [
            {
                "description": "Data analysis",
                "quantity": "3",
                "unit_price": "250.00",
                "vat_rate": "21",
                "total": "750.00",
            }
        ],
    },

    {
        "id": "invoice_003",
        "invoice_number": "CLOUD-4402",
        "invoice_date": "2026-07-15",
        "due_date": "2026-07-29",
        "supplier": {
            "name": "CloudWorks Europe B.V.",
            "address": (
                "Science Park 55, "
                "1098 XH Amsterdam, Netherlands"
            ),
            "vat_number": "NL777888999B01",
        },
        "customer": {
            "name": "Northwind AI B.V.",
            "address": (
                "Grote Markt 20, "
                "9712 HV Groningen, Netherlands"
            ),
            "vat_number": "NL333222111B01",
        },
        "currency": "EUR",
        "subtotal": "1800.00",
        "vat_amount": "378.00",
        "total_amount": "2178.00",
        "line_items": [
            {
                "description": "Cloud hosting",
                "quantity": "1",
                "unit_price": "1200.00",
                "vat_rate": "21",
                "total": "1200.00",
            },
            {
                "description": "Monitoring support",
                "quantity": "2",
                "unit_price": "300.00",
                "vat_rate": "21",
                "total": "600.00",
            },
        ],
    },

    {
        "id": "invoice_004",
        "invoice_number": "ML-00991",
        "invoice_date": "2026-06-10",
        "due_date": "2026-07-10",
        "supplier": {
            "name": (
                "Machine Learning Partners B.V."
            ),
            "address": (
                "Europalaan 31, "
                "3526 KS Utrecht, Netherlands"
            ),
            "vat_number": "NL909090909B01",
        },
        "customer": {
            "name": "Vision Systems B.V.",
            "address": (
                "Oude Ebbingestraat 50, "
                "9712 HL Groningen, Netherlands"
            ),
            "vat_number": "NL121212121B01",
        },
        "currency": "EUR",
        "subtotal": "2450.00",
        "vat_amount": "514.50",
        "total_amount": "2964.50",
        "line_items": [
            {
                "description": "Model development",
                "quantity": "10",
                "unit_price": "175.00",
                "vat_rate": "21",
                "total": "1750.00",
            },
            {
                "description": "Deployment support",
                "quantity": "4",
                "unit_price": "175.00",
                "vat_rate": "21",
                "total": "700.00",
            },
        ],
    },

    {
        "id": "invoice_005",
        "invoice_number": "DOC-2026-77",
        "invoice_date": "2026-09-18",
        "due_date": "2026-10-18",
        "supplier": {
            "name": (
                "Document Intelligence B.V."
            ),
            "address": (
                "Paterswoldseweg 806, "
                "9728 BM Groningen, Netherlands"
            ),
            "vat_number": "NL565656565B01",
        },
        "customer": {
            "name": "Automation Factory B.V.",
            "address": (
                "Industrieweg 40, "
                "9403 AB Assen, Netherlands"
            ),
            "vat_number": "NL787878787B01",
        },
        "currency": "EUR",
        "subtotal": "1320.00",
        "vat_amount": "277.20",
        "total_amount": "1597.20",
        "line_items": [
            {
                "description": (
                    "Document extraction prototype"
                ),
                "quantity": "8",
                "unit_price": "120.00",
                "vat_rate": "21",
                "total": "960.00",
            },
            {
                "description": "API integration",
                "quantity": "3",
                "unit_price": "120.00",
                "vat_rate": "21",
                "total": "360.00",
            },
        ],
    },

    {
        "id": "invoice_006",
        "invoice_number": "NORTH-006",
        "invoice_date": "2026-09-20",
        "due_date": None,
        "supplier": {
            "name": (
                "Northern Data Services B.V."
            ),
            "address": (
                "Peizerweg 97, "
                "9727 AJ Groningen, Netherlands"
            ),
            "vat_number": "NL101010101B01",
        },
        "customer": {
            "name": "Example Logistics B.V.",
            "address": (
                "Europaweg 12, "
                "9723 AS Groningen, Netherlands"
            ),
            "vat_number": None,
        },
        "currency": "EUR",
        "subtotal": "500.00",
        "vat_amount": "105.00",
        "total_amount": "605.00",
        "line_items": [
            {
                "description": (
                    "Data pipeline maintenance"
                ),
                "quantity": "4",
                "unit_price": "125.00",
                "vat_rate": "21",
                "total": "500.00",
            }
        ],
    },

    {
        "id": "invoice_007",
        "invoice_number": "US-2026-884",
        "invoice_date": "2026-09-05",
        "due_date": "2026-10-05",
        "supplier": {
            "name": "Vector Cloud Inc.",
            "address": (
                "500 Market Street, "
                "San Francisco, CA 94105, USA"
            ),
            "vat_number": "US99887766",
        },
        "customer": {
            "name": "European AI Labs B.V.",
            "address": (
                "Kadijk 22, "
                "9712 AA Groningen, Netherlands"
            ),
            "vat_number": "NL232323232B01",
        },
        "currency": "USD",
        "subtotal": "3250.00",
        "vat_amount": "682.50",
        "total_amount": "3932.50",
        "line_items": [
            {
                "description": "GPU compute",
                "quantity": "10",
                "unit_price": "200.00",
                "vat_rate": "21",
                "total": "2000.00",
            },
            {
                "description": "Object storage",
                "quantity": "5",
                "unit_price": "100.00",
                "vat_rate": "21",
                "total": "500.00",
            },
            {
                "description": (
                    "Technical support"
                ),
                "quantity": "3",
                "unit_price": "250.00",
                "vat_rate": "21",
                "total": "750.00",
            },
        ],
    },

    {
        "id": "invoice_008",
        "invoice_number": "MESSY-2026-42",
        "invoice_date": "2026-09-11",
        "due_date": "2026-10-11",
        "supplier": {
            "name": "Messy Documents B.V.",
            "address": (
                "Damsterdiep 100, "
                "9713 EL Groningen, Netherlands"
            ),
            "vat_number": "NL454545454B01",
        },
        "customer": {
            "name": "AI Integration B.V.",
            "address": (
                "Helperpark 44, "
                "9723 ZA Groningen, Netherlands"
            ),
            "vat_number": "NL676767676B01",
        },
        "currency": "EUR",
        "subtotal": "1650.00",
        "vat_amount": "346.50",
        "total_amount": "1996.50",
        "line_items": [
            {
                "description": (
                    "Document processing"
                ),
                "quantity": "10",
                "unit_price": "120.00",
                "vat_rate": "21",
                "total": "1200.00",
            },
            {
                "description": "Integration work",
                "quantity": "3",
                "unit_price": "150.00",
                "vat_rate": "21",
                "total": "450.00",
            },
        ],
    },

    {
        "id": "invoice_009",
        "invoice_number": "VAT-MIX-2026-09",
        "invoice_date": "2026-09-22",
        "due_date": "2026-10-22",
        "supplier": {
            "name": "Mixed VAT Services B.V.",
            "address": (
                "Nieuwe Ebbingestraat 15, "
                "9712 ND Groningen, Netherlands"
            ),
            "vat_number": "NL919191919B01",
        },
        "customer": {
            "name": "Example Commerce B.V.",
            "address": (
                "Hereweg 80, "
                "9725 AG Groningen, Netherlands"
            ),
            "vat_number": "NL818181818B01",
        },
        "currency": "EUR",

        "subtotal": "350.00",
        "vat_amount": "49.50",

        "vat_breakdown": [
            {
                "rate": "21",
                "taxable_amount": "150.00",
                "vat_amount": "31.50",
            },
            {
                "rate": "9",
                "taxable_amount": "200.00",
                "vat_amount": "18.00",
            },
        ],

        "total_amount": "399.50",

        "line_items": [
            {
                "description": "Software service",
                "quantity": "1",
                "unit_price": "100.00",
                "vat_rate": "21",
                "total": "100.00",
            },
            {
                "description": (
                    "Printed publication"
                ),
                "quantity": "2",
                "unit_price": "100.00",
                "vat_rate": "9",
                "total": "200.00",
            },
            {
                "description": (
                    "Technical support"
                ),
                "quantity": "1",
                "unit_price": "50.00",
                "vat_rate": "21",
                "total": "50.00",
            },
        ],
    },
]


def create_pdf(
    invoice: dict,
    path: Path,
) -> None:
    document = pymupdf.open()

    page = document.new_page(
        width=595,
        height=842,
    )

    lines = [
        "INVOICE",
        "",
        invoice["supplier"]["name"],
        invoice["supplier"]["address"],
    ]

    if invoice["supplier"].get(
        "vat_number"
    ):
        lines.append(
            f'VAT: '
            f'{invoice["supplier"]["vat_number"]}'
        )

    lines.extend(
        [
            "",
            "Bill to:",
            invoice["customer"]["name"],
            invoice["customer"]["address"],
        ]
    )

    if invoice["customer"].get(
        "vat_number"
    ):
        lines.append(
            f'VAT: '
            f'{invoice["customer"]["vat_number"]}'
        )

    lines.extend(
        [
            "",
            (f'Invoice number: '
            f'{invoice["invoice_number"]}'),
            (f'Invoice date: '
            f'{invoice["invoice_date"]}'),
        ]
    )

    if invoice.get("due_date"):
        lines.append(
            f'Due date: {invoice["due_date"]}'
        )

    lines.extend(
        [
            f'Currency: {invoice["currency"]}',
            "",
            (
                "Description | Quantity | "
                "Unit price | VAT | Total"
            ),
        ]
    )

    for item in invoice["line_items"]:
        lines.append(
            f'{item["description"]} | '
            f'{item["quantity"]} | '
            f'{invoice["currency"]} '
            f'{item["unit_price"]} | '
            f'{item["vat_rate"]}% | '
            f'{invoice["currency"]} '
            f'{item["total"]}'
        )

    lines.append("")

    lines.append(
        f'Subtotal: '
        f'{invoice["currency"]} '
        f'{invoice["subtotal"]}'
    )

    if invoice.get("vat_breakdown"):
        lines.append("VAT breakdown:")

        for vat in invoice[
            "vat_breakdown"
        ]:
            lines.append(
                f'VAT {vat["rate"]}% '
                f'on {invoice["currency"]} '
                f'{vat["taxable_amount"]}: '
                f'{invoice["currency"]} '
                f'{vat["vat_amount"]}'
            )

    lines.append(
        f'VAT total: '
        f'{invoice["currency"]} '
        f'{invoice["vat_amount"]}'
    )

    lines.append(
        f'Total: '
        f'{invoice["currency"]} '
        f'{invoice["total_amount"]}'
    )

    y = 60

    for line in lines:
        page.insert_text(
            (60, y),
            line,
            fontsize=10,
        )

        y += 18

    document.save(path)
    document.close()


def create_messy_pdf(
    invoice: dict,
    path: Path,
) -> None:
    document = pymupdf.open()

    page = document.new_page(
        width=595,
        height=842,
    )

    page.insert_text(
        (50, 60),
        "INVOICE",
        fontsize=16,
    )

    page.insert_text(
        (50, 100),
        invoice["supplier"]["name"],
        fontsize=10,
    )

    page.insert_text(
        (50, 118),
        invoice["supplier"]["address"],
        fontsize=10,
    )

    page.insert_text(
        (50, 136),
        (
            f'VAT: '
            f'{invoice["supplier"]["vat_number"]}'
        ),
        fontsize=10,
    )

    page.insert_text(
        (330, 100),
        (
            f'Invoice number: '
            f'{invoice["invoice_number"]}'
        ),
        fontsize=10,
    )

    page.insert_text(
        (330, 118),
        (
            f'Invoice date: '
            f'{invoice["invoice_date"]}'
        ),
        fontsize=10,
    )

    page.insert_text(
        (330, 136),
        (
            f'Due date: '
            f'{invoice["due_date"]}'
        ),
        fontsize=10,
    )

    page.insert_text(
        (50, 180),
        "Bill to:",
        fontsize=10,
    )

    page.insert_text(
        (50, 198),
        invoice["customer"]["name"],
        fontsize=10,
    )

    page.insert_text(
        (50, 216),
        invoice["customer"]["address"],
        fontsize=10,
    )

    page.insert_text(
        (50, 234),
        (
            f'VAT: '
            f'{invoice["customer"]["vat_number"]}'
        ),
        fontsize=10,
    )

    page.insert_text(
        (330, 216),
        (
            f'Currency: '
            f'{invoice["currency"]}'
        ),
        fontsize=10,
    )

    y = 300

    for item in invoice["line_items"]:
        line = (
            f'{item["description"]}   '
            f'{item["quantity"]}   '
            f'{invoice["currency"]} '
            f'{item["unit_price"]}   '
            f'{item["vat_rate"]}%   '
            f'{invoice["currency"]} '
            f'{item["total"]}'
        )

        page.insert_text(
            (50, y),
            line,
            fontsize=9,
        )

        y += 20

    page.insert_text(
        (330, y + 30),
        (
            f'Subtotal: '
            f'{invoice["currency"]} '
            f'{invoice["subtotal"]}'
        ),
        fontsize=10,
    )

    page.insert_text(
        (330, y + 48),
        (
            f'VAT: '
            f'{invoice["currency"]} '
            f'{invoice["vat_amount"]}'
        ),
        fontsize=10,
    )

    page.insert_text(
        (330, y + 66),
        (
            f'Total: '
            f'{invoice["currency"]} '
            f'{invoice["total_amount"]}'
        ),
        fontsize=10,
    )

    document.save(path)
    document.close()


def main() -> None:
    for invoice in INVOICES:
        invoice_id = invoice["id"]

        pdf_path = (
            INVOICE_DIR
            / f"{invoice_id}.pdf"
        )

        json_path = (
            GROUND_TRUTH_DIR
            / f"{invoice_id}.json"
        )

        if invoice_id == "invoice_008":
            create_messy_pdf(
                invoice,
                pdf_path,
            )
        else:
            create_pdf(
                invoice,
                pdf_path,
            )

        ground_truth = {
            key: value
            for key, value in invoice.items()
            if key != "id"
        }

        json_path.write_text(
            json.dumps(
                ground_truth,
                indent=2,
            ),
            encoding="utf-8",
        )

        print(
            f"Created {invoice_id}"
        )

    print()

    print(
        f"Created {len(INVOICES)} "
        "evaluation invoices."
    )


if __name__ == "__main__":
    main()