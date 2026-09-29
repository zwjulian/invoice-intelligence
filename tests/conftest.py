import os
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------
# IMPORTANT:
# Configure the test environment BEFORE importing application modules.
#
# This ensures pytest never connects to the real Render PostgreSQL
# database, even when DATABASE_URL exists in the local .env file.
# ---------------------------------------------------------------------

TEST_DATABASE_PATH = (
    Path(tempfile.gettempdir())
    / "invoice_intelligence_pytest.db"
)


# Remove a database left behind by an interrupted previous test run.
if TEST_DATABASE_PATH.exists():
    TEST_DATABASE_PATH.unlink()


os.environ["DATABASE_URL"] = (
    f"sqlite:///{TEST_DATABASE_PATH.as_posix()}"
)

os.environ["USE_MOCK_LLM"] = "true"


# These imports must happen AFTER the environment variables above.
import app.db_models  # noqa: F401
from app.database import (
    Base,
    engine,
)


@pytest.fixture(
    scope="session",
    autouse=True,
)
def test_database_schema():
    """
    Create a completely isolated SQLite schema for the test session.

    All SQLAlchemy models registered in app.db_models are created,
    including invoices and invoice_line_items.
    """

    Base.metadata.drop_all(
        bind=engine
    )

    Base.metadata.create_all(
        bind=engine
    )

    yield

    Base.metadata.drop_all(
        bind=engine
    )

    engine.dispose()

    if TEST_DATABASE_PATH.exists():
        try:
            TEST_DATABASE_PATH.unlink()
        except PermissionError:
            # Windows can briefly keep a SQLite file handle open.
            # The file lives in the temporary directory and will
            # also be removed before the next test session.
            pass


@pytest.fixture(
    autouse=True,
)
def clean_test_database(
    test_database_schema,
):
    """
    Start every test with empty database tables.

    This prevents tests from influencing each other and makes
    duplicate detection deterministic.
    """

    with engine.begin() as connection:
        for table in reversed(
            Base.metadata.sorted_tables
        ):
            connection.execute(
                table.delete()
            )

    yield