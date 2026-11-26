"""Database engine and session management."""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, text
from sqlmodel import Session, SQLModel, create_engine

from ticket_mcp import models  # noqa: F401  (registers tables on SQLModel.metadata)

logger = logging.getLogger(__name__)

_engine: Engine | None = None


def init_engine(database_url: str) -> Engine:
    """Create (or replace) the global engine. Creates the SQLite folder if needed."""
    global _engine
    if _engine is not None:
        _engine.dispose()

    if database_url.startswith("sqlite:///"):
        db_path = database_url.removeprefix("sqlite:///")
        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    _engine = create_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
    )
    return _engine


def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("Database engine not initialised. Call init_engine() first.")
    return _engine


def create_tables() -> None:
    SQLModel.metadata.create_all(get_engine())


def drop_tables() -> None:
    SQLModel.metadata.drop_all(get_engine())


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transactional session: commits on success, rolls back on error."""
    session = Session(get_engine(), expire_on_commit=False)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ping() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:  # pragma: no cover - defensive
        logger.exception("Database ping failed")
        return False


def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
