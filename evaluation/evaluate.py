import json
from decimal import Decimal
from pathlib import Path

from app.services.llm_service import (
    GeminiInvoiceExtractor,
)
from app.services.pdf_service import (
    extract_text_from_pdf,
)


ROOT = Path(__file__).resolve().parent.parent

INVOICE_DIR = (
    ROOT / "evaluation" / "invoices"
)

GROUND_TRUTH_DIR = (
    ROOT / "evaluation" / "ground_truth"
)


FIELDS = [
    "invoice_number",
    "invoice_date",
    "due_date",
    "currency",
    "subtotal",
    "vat_amount",
    "total_amount",
    "supplier_name",
    "supplier_vat_number",
    "customer_name",
    "customer_vat_number",
    "line_items",
    "vat_breakdown",
]


def normalize_text(
    value,
) -> str | None:
    if value is None:
        return None

    return str(value).strip().casefold()


def compare_money(
    predicted,
    expected,
) -> bool:
    if (
        predicted is None
        or expected is None
    ):
        return predicted is None and expected is None

    return (
        Decimal(str(predicted))
        == Decimal(str(expected))
    )


def compare_date(
    predicted,
    expected,
) -> bool:
    if (
        predicted is None
        or expected is None
    ):
        return predicted is None and expected is None

    return (
        str(predicted)
        == str(expected)
    )


def compare_line_items(
    predicted_items,
    expected_items,
) -> bool:
    if len(predicted_items) != len(
        expected_items
    ):
        return False

    for predicted, expected in zip(
        predicted_items,
        expected_items,
    ):
        if (
            normalize_text(
                predicted.description
            )
            != normalize_text(
                expected["description"]
            )
        ):
            return False

        if not compare_money(
            predicted.quantity,
            expected["quantity"],
        ):
            return False

        if not compare_money(
            predicted.unit_price,
            expected["unit_price"],
        ):
            return False

        if not compare_money(
            predicted.vat_rate,
            expected["vat_rate"],
        ):
            return False

        if not compare_money(
            predicted.total,
            expected["total"],
        ):
            return False

    return True


def compare_vat_breakdown(
    predicted_breakdown,
    expected_breakdown,
) -> bool:
    if len(predicted_breakdown) != len(
        expected_breakdown
    ):
        return False

    predicted_by_rate = {
        Decimal(str(item.rate)): item
        for item in predicted_breakdown
    }

    for expected in expected_breakdown:
        expected_rate = Decimal(
            str(expected["rate"])
        )

        predicted = predicted_by_rate.get(
            expected_rate
        )

        if predicted is None:
            return False

        if not compare_money(
            predicted.taxable_amount,
            expected["taxable_amount"],
        ):
            return False

        if not compare_money(
            predicted.vat_amount,
            expected["vat_amount"],
        ):
            return False

    return True


def evaluate_invoice(
    predicted,
    expected: dict,
) -> dict[str, bool]:
    results: dict[str, bool] = {}

    results["invoice_number"] = (
        normalize_text(
            predicted.invoice_number
        )
        == normalize_text(
            expected["invoice_number"]
        )
    )

    results["invoice_date"] = (
        compare_date(
            predicted.invoice_date,
            expected["invoice_date"],
        )
    )

    results["due_date"] = (
        compare_date(
            predicted.due_date,
            expected["due_date"],
        )
    )

    results["currency"] = (
        normalize_text(
            predicted.currency
        )
        == normalize_text(
            expected["currency"]
        )
    )

    results["subtotal"] = (
        compare_money(
            predicted.subtotal,
            expected["subtotal"],
        )
    )

    results["vat_amount"] = (
        compare_money(
            predicted.vat_amount,
            expected["vat_amount"],
        )
    )

    results["total_amount"] = (
        compare_money(
            predicted.total_amount,
            expected["total_amount"],
        )
    )

    results["supplier_name"] = (
        normalize_text(
            predicted.supplier.name
        )
        == normalize_text(
            expected["supplier"]["name"]
        )
    )

    results["supplier_vat_number"] = (
        normalize_text(
            predicted.supplier.vat_number
        )
        == normalize_text(
            expected["supplier"][
                "vat_number"
            ]
        )
    )

    predicted_customer = (
        predicted.customer
    )

    results["customer_name"] = (
        normalize_text(
            predicted_customer.name
            if predicted_customer
            else None
        )
        == normalize_text(
            expected["customer"]["name"]
        )
    )

    results[
        "customer_vat_number"
    ] = (
        normalize_text(
            predicted_customer.vat_number
            if predicted_customer
            else None
        )
        == normalize_text(
            expected["customer"][
                "vat_number"
            ]
        )
    )

    results["line_items"] = (
        compare_line_items(
            predicted.line_items,
            expected["line_items"],
        )
    )

    if "vat_breakdown" in expected:
        results["vat_breakdown"] = (
            compare_vat_breakdown(
                predicted.vat_breakdown,
                expected["vat_breakdown"],
            )
        )

    return results


def main() -> None:
    extractor = GeminiInvoiceExtractor()

    field_correct = {
        field: 0
        for field in FIELDS
    }

    field_total = {
        field: 0
        for field in FIELDS
    }

    invoice_results = []

    pdf_files = sorted(
        INVOICE_DIR.glob("*.pdf")
    )

    print(
        f"Evaluating {len(pdf_files)} "
        "invoices..."
    )

    print()

    for pdf_path in pdf_files:
        invoice_id = pdf_path.stem

        ground_truth_path = (
            GROUND_TRUTH_DIR
            / f"{invoice_id}.json"
        )

        expected = json.loads(
            ground_truth_path.read_text(
                encoding="utf-8"
            )
        )

        print(
            f"Processing {invoice_id}..."
        )

        text = extract_text_from_pdf(
            pdf_path
        )

        predicted = extractor.extract(
            text
        )

        results = evaluate_invoice(
            predicted,
            expected,
        )

        for field, correct in (
            results.items()
        ):
            field_total[field] += 1

            if correct:
                field_correct[field] += 1

        invoice_accuracy = (
            sum(results.values())
            / len(results)
        )

        invoice_results.append(
            {
                "invoice": invoice_id,
                "accuracy": invoice_accuracy,
                "fields": results,
            }
        )

        print(
            f"  Accuracy: "
            f"{invoice_accuracy * 100:.1f}%"
        )

    print()

    print("=" * 55)
    print("FIELD-LEVEL RESULTS")
    print("=" * 55)

    total_correct = 0
    total_fields = 0

    for field in FIELDS:
        total = field_total[field]

        if total == 0:
            continue

        correct = field_correct[field]

        accuracy = (
            correct / total
        )

        total_correct += correct
        total_fields += total

        print(
            f"{field:<25} "
            f"{correct}/{total} "
            f"({accuracy * 100:6.1f}%)"
        )

    overall_accuracy = (
        total_correct / total_fields
        if total_fields
        else 0
    )

    print("-" * 55)

    print(
        f"{'Overall':<25} "
        f"{total_correct}/{total_fields} "
        f"({overall_accuracy * 100:6.1f}%)"
    )

    output = {
        "overall_accuracy": (
            overall_accuracy
        ),
        "field_accuracy": {
            field: (
                field_correct[field]
                / field_total[field]
            )
            for field in FIELDS
            if field_total[field] > 0
        },
        "invoices": invoice_results,
    }

    output_path = (
        ROOT
        / "evaluation"
        / "results.json"
    )

    output_path.write_text(
        json.dumps(
            output,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()

    print(
        f"Results saved to "
        f"{output_path}"
    )


if __name__ == "__main__":
    main()