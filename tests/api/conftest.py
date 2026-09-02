"""Fixtures for the API contract tests.

These need a real PostgreSQL: the schema uses JSONB, and viewing capacity is
enforced by a plpgsql trigger that takes a row lock, which is the thing the
concurrency test exists to prove. Faking that on SQLite would test a different
system.

Set TEST_DATABASE_URL (or DATABASE_URL) to run them. Without it they skip with a
message rather than passing quietly.

The schema is built by running the migration, so the migration is under test too
and not just the models.
"""

from __future__ import annotations

import datetime as dt
import os
from collections.abc import Iterator

import pytest
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

TABLES = (
    "decisions",
    "application_units",
    "viewing_bookings",
    "viewings",
    "offers",
    "housing_need",
    "household_members",
    "applications",
    "units",
    "properties",
)


def _url() -> str | None:
    return os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")


requires_db = pytest.mark.skipif(
    _url() is None,
    reason="needs PostgreSQL: set TEST_DATABASE_URL (see tests/api/conftest.py)",
)


@pytest.fixture(scope="session")
def database_url() -> str:
    url = _url()
    if url is None:
        pytest.skip("needs PostgreSQL: set TEST_DATABASE_URL")
    return url


@pytest.fixture(scope="session")
def engine(database_url: str) -> Iterator[Engine]:
    """A schema built by the migration, torn down afterwards."""
    from alembic.config import Config

    from alembic import command

    os.environ["DATABASE_URL"] = database_url

    raw = create_engine(database_url, poolclass=None)
    with raw.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))

    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")

    yield raw
    raw.dispose()


@pytest.fixture(autouse=True)
def clean_tables(request: pytest.FixtureRequest) -> Iterator[None]:
    """Empty every table between tests so ordering cannot matter."""
    if "engine" not in request.fixturenames:
        yield
        return
    engine: Engine = request.getfixturevalue("engine")
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {', '.join(TABLES)} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with sessionmaker(bind=engine, expire_on_commit=False)() as db:
        yield db


@pytest.fixture
def seeded(session: Session) -> Session:
    """The demo stock loaded, which is what the search endpoints are tested against."""
    from seeds.load import load

    load(session)
    session.commit()
    return session


@pytest.fixture
def client(engine: Engine):  # noqa: ANN201 - TestClient, imported lazily
    from fastapi.testclient import TestClient

    from api.app import cache, db
    from api.app.main import app

    # The app builds its own engine from DATABASE_URL, which the engine fixture
    # has already pointed at the test database. Clear the memoised one so a test
    # session cannot inherit an engine from a previous configuration.
    db.get_engine.cache_clear()
    db.get_sessionmaker.cache_clear()
    cache.reset_for_tests()

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def application_token(client, seeded) -> str:  # noqa: ANN001
    response = client.post("/api/applications", json={"contact_name": "Testi Hakija"})
    assert response.status_code == 201
    token: str = response.json()["edit_token"]
    return token


@pytest.fixture
def unit_ids(client, seeded) -> dict[str, int]:  # noqa: ANN001
    """One rental unit id per housing form, plus a sale unit."""
    found: dict[str, int] = {}
    units = client.get("/api/units", params={"limit": 200}).json()["units"]
    for unit in units:
        key = unit["housing_form"] if unit["listing_type"] == "vuokra" else "myynti"
        found.setdefault(key, unit["id"])
    return found


@pytest.fixture
def now() -> dt.datetime:
    return dt.datetime.now(dt.UTC)
