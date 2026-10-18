import os
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import get_settings

settings = get_settings()

db_url = settings.DATABASE_URL

# For SQLite, ensure foreign keys are enabled and same-thread checks disabled
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

if db_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a database session and safely closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """Utility to create tables (primarily used in tests)."""
    Base.metadata.create_all(bind=engine)


def drop_all_tables():
    """Utility to drop tables (primarily used in test teardowns)."""
    Base.metadata.drop_all(bind=engine)
