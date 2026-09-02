"""Database session handling.

One engine per process, sessions per request. Synchronous on purpose: the rule
engine is pure computation and the queries are small, so an async stack would add
a driver, a test plugin and a class of flakiness without buying anything here.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


class DatabaseNotConfigured(RuntimeError):
    pass


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise DatabaseNotConfigured(
            "DATABASE_URL is not set. Locally: docker compose up -d, then "
            "DATABASE_URL=postgresql+psycopg://asuntohaku:asuntohaku@localhost:5432/asuntohaku"
        )
    return url


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    # pool_pre_ping because serverless functions keep connections across freezes
    # and Neon closes idle ones.
    return create_engine(database_url(), pool_pre_ping=True, pool_size=5, max_overflow=5)


@lru_cache(maxsize=1)
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """FastAPI dependency: a session per request, rolled back on error."""
    with get_sessionmaker()() as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
