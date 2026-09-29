from sqlalchemy import inspect, text

from app.db.database import engine


def print_table_structure(
    inspector,
    table_name: str,
) -> None:
    print()
    print("=" * 70)
    print(f"TABLE: {table_name}")
    print("=" * 70)

    columns = inspector.get_columns(table_name)

    print()
    print("COLUMNS")

    for column in columns:
        print(
            f"  {column['name']:<25} "
            f"{column['type']!s:<25} "
            f"nullable={column['nullable']}"
        )

    primary_key = inspector.get_pk_constraint(
        table_name
    )

    print()
    print("PRIMARY KEY")
    print(
        f"  {primary_key.get('constrained_columns', [])}"
    )

    foreign_keys = inspector.get_foreign_keys(
        table_name
    )

    print()
    print("FOREIGN KEYS")

    if not foreign_keys:
        print("  None")
    else:
        for foreign_key in foreign_keys:
            print(
                f"  {foreign_key['constrained_columns']} "
                f"-> "
                f"{foreign_key['referred_table']}."
                f"{foreign_key['referred_columns']}"
            )


def print_row_count(
    table_name: str,
) -> None:
    with engine.connect() as connection:
        result = connection.execute(
            text(
                f'SELECT COUNT(*) FROM "{table_name}"'
            )
        )

        count = result.scalar_one()

    print()
    print(f"ROWS: {count}")


def main() -> None:
    print("Inspecting database...")

    inspector = inspect(engine)

    tables = inspector.get_table_names()

    print()
    print("Tables found:")

    for table in tables:
        print(f"  - {table}")

    for table in tables:
        print_table_structure(
            inspector,
            table,
        )

        if table != "alembic_version":
            print_row_count(table)

    print()
    print("=" * 70)
    print("Inspection completed.")
    print("=" * 70)


if __name__ == "__main__":
    main()