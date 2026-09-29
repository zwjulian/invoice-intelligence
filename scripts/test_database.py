from sqlalchemy import inspect, text

from app.db.database import engine


def main() -> None:
    print("Testing database connection...")
    print()

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT 1")
            )

            value = result.scalar_one()

            print(
                f"Database query result: {value}"
            )

        inspector = inspect(engine)

        tables = inspector.get_table_names()

        print()
        print("Connection successful.")
        print()

        if tables:
            print("Tables found:")

            for table in tables:
                print(f"  - {table}")
        else:
            print(
                "Connection works, but no tables exist yet."
            )

    except Exception as exc:
        print()
        print("DATABASE CONNECTION FAILED")
        print()
        print(exc)

        raise


if __name__ == "__main__":
    main()