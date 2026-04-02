from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import config
import os

DATABASE_URL = f"sqlite:///{config.db_path}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist, then run lightweight inline migrations."""
    from app import models  # noqa: F401 – ensure models are registered
    Base.metadata.create_all(bind=engine)
    _run_migrations()


def _run_migrations():
    """Apply additive schema changes that SQLAlchemy create_all won't handle on existing DBs."""
    with engine.connect() as conn:
        # Add exchange_order_id to trades if it doesn't exist yet
        existing = conn.execute(
            __import__('sqlalchemy').text("PRAGMA table_info(trades)")
        ).fetchall()
        col_names = [row[1] for row in existing]
        if "exchange_order_id" not in col_names:
            conn.execute(
                __import__('sqlalchemy').text(
                    "ALTER TABLE trades ADD COLUMN exchange_order_id TEXT"
                )
            )
            conn.commit()
