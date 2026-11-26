import pytest

from ticket_mcp import repository as repo
from ticket_mcp.db import session_scope
from ticket_mcp.models import Priority, ProductFamily, Status
from ticket_mcp.seed import SAMPLE_TICKETS, seed_if_empty


def _register(**overrides):
    data = dict(
        title="Switch port errors",
        description="CRC errors on Gi1/0/1",
        product_family=ProductFamily.SWITCHES,
        priority=Priority.P3,
        registered_by="Priya Nair",
    )
    data.update(overrides)
    with session_scope() as s:
        return repo.register_ticket(s, **data)


def test_register_assigns_id_and_defaults():
    t = _register()
    assert t.ticket_id == "TKT-10001"
    assert t.status == Status.OPEN
    assert t.ticket_date is not None and t.resolved_date is None


@pytest.mark.parametrize("raw,pk", [("TKT-10001", 1), ("tkt-10042", 42), ("10003", 3)])
def test_parse_ticket_id(raw, pk):
    assert repo.parse_ticket_id(raw) == pk


@pytest.mark.parametrize("raw", ["", "ABC", "TKT-10000", "TKT-9"])
def test_parse_ticket_id_invalid(raw):
    with pytest.raises(repo.InvalidTicketIdError):
        repo.parse_ticket_id(raw)


def test_get_missing_ticket():
    with session_scope() as s, pytest.raises(repo.TicketNotFoundError):
        repo.get_ticket(s, "TKT-19999")


def test_search_filters_are_case_insensitive_partial():
    _register(title="BGP flapping", product_family=ProductFamily.ROUTERS, registered_by="Anita Sharma")
    _register(title="VLAN missing", registered_by="John Mathew")
    with session_scope() as s:
        total, rows = repo.search_tickets(s, keyword="bgp")
        assert total == 1 and rows[0].title == "BGP flapping"
        total, _ = repo.search_tickets(s, registered_by="ANITA")
        assert total == 1
        total, _ = repo.search_tickets(s, product_family=ProductFamily.SWITCHES)
        assert total == 1
        total, _ = repo.search_tickets(s, date_from="2000-01-01", date_to="2999-12-31")
        assert total == 2


def test_search_pagination():
    for i in range(5):
        _register(title=f"Ticket {i}")
    with session_scope() as s:
        total, rows = repo.search_tickets(s, limit=2, offset=1)
    assert total == 5 and len(rows) == 2


def test_resolve_and_lifecycle():
    t = _register()
    with session_scope() as s:
        repo.update_ticket_status(s, t.ticket_id, status=Status.IN_PROGRESS)
        resolved = repo.resolve_ticket(s, t.ticket_id, resolved_by="Vikram", remarks="Cable replaced")
        assert resolved.status == Status.RESOLVED
        assert resolved.resolved_by == "Vikram" and resolved.resolved_date is not None
        assert "Cable replaced" in resolved.remarks

        reopened = repo.update_ticket_status(s, t.ticket_id, status=Status.OPEN, remarks="Issue back")
        assert reopened.resolved_by is None and reopened.resolved_date is None


def test_invalid_transitions():
    t = _register()
    with session_scope() as s:
        with pytest.raises(repo.InvalidTransitionError):
            repo.update_ticket_status(s, t.ticket_id, status=Status.CLOSED)  # Open -> Closed
        with pytest.raises(repo.InvalidTransitionError):
            repo.update_ticket_status(s, t.ticket_id, status=Status.RESOLVED)  # must use resolve_ticket


def test_closed_is_final():
    t = _register()
    with session_scope() as s:
        repo.resolve_ticket(s, t.ticket_id, resolved_by="A", remarks="done")
        repo.update_ticket_status(s, t.ticket_id, status=Status.CLOSED)
        with pytest.raises(repo.InvalidTransitionError):
            repo.update_ticket_status(s, t.ticket_id, status=Status.OPEN)


def test_seed_only_when_empty():
    assert seed_if_empty() == len(SAMPLE_TICKETS)
    assert seed_if_empty() == 0
    with session_scope() as s:
        stats = repo.ticket_stats(s)
    assert stats["total"] == len(SAMPLE_TICKETS)
    assert sum(stats["by_status"].values()) == len(SAMPLE_TICKETS)
