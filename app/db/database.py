from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


def normalize_database_url(database_url: str) -> str:
    """
    Convert a normal PostgreSQL URL into the SQLAlchemy psycopg format.

    Render commonly provides URLs starting with:
        postgres://
    or:
        postgresql://

    SQLAlchemy with psycopg uses:
        postgresql+psycopg://
    """

    if database_url.startswith("postgres://"):
        return database_url.replace(
            "postgres://",
            "postgresql+psycopg://",
            1,
        )

    if database_url.startswith("postgresql://"):
        return database_url.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    return database_url


DATABASE_URL = normalize_database_url(
    settings.database_url
)


connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
    }


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that creates a database session
    for a request and always closes it afterwards.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()