"""Database configuration and session management."""

import os
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# For SQLite, we need check_same_thread=False for async usage
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)


def get_db() -> Generator[Session, None, None]:
    """Get database session dependency."""
    with Session(engine) as session:
        yield session


def init_db() -> None:
    """Initialize database tables."""
    # Import models to ensure they are registered with SQLModel
    from app import models  # noqa: F401

    SQLModel.metadata.create_all(engine)
