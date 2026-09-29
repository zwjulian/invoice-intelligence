from sqlalchemy import inspect

from app.db.database import Base, engine


def main() -> None:
    print("Creating database tables...")

    Base.metadata.create_all(
        bind=engine
    )

    inspector = inspect(engine)

    tables = inspector.get_table_names()

    print()
    print("Database tables:")

    for table in tables:
        print(f"  - {table}")

    print()
    print("Database initialization completed.")


if __name__ == "__main__":
    main()