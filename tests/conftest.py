from collections.abc import Iterator

import ticket_mcp  # noqa: F401  (import first: installs warning filters before fastmcp loads)

import pytest
from fastmcp import FastMCP

from ticket_mcp import db
from ticket_mcp.server import create_server


@pytest.fixture(autouse=True)
def database(tmp_path) -> Iterator[None]:
    """Fresh SQLite file per test."""
    db.init_engine(f"sqlite:///{tmp_path / 'test.db'}")
    db.create_tables()
    yield
    db.dispose_engine()


@pytest.fixture
def mcp() -> FastMCP:
    return create_server("test-server")


@pytest.fixture
def new_ticket() -> dict:
    return {
        "title": "Router down",
        "description": "Edge router RTR-01 unreachable",
        "product_family": "Routers",
        "priority": "P1",
        "registered_by": "Ramkumar",
    }
