"""MCP Resources: read-only data the client can load into context."""

from fastmcp import FastMCP
from fastmcp.exceptions import ResourceError

from ticket_mcp import repository as repo
from ticket_mcp.db import session_scope
from ticket_mcp.models import Priority, ProductFamily, Status, TicketRead

RECENT_LIMIT = 10


def register_resources(mcp: FastMCP) -> None:
    @mcp.resource(
        "tickets://reference",
        name="ticket_reference",
        description="Allowed values for product family, priority and status, plus status transitions.",
        mime_type="application/json",
    )
    def reference() -> dict:
        return {
            "product_families": [f.value for f in ProductFamily],
            "priorities": [p.value for p in Priority],
            "statuses": [s.value for s in Status],
            "status_transitions": {
                src.value: [dst.value for dst in dsts] for src, dsts in repo.ALLOWED_TRANSITIONS.items()
            },
            "ticket_id_format": "TKT-10001",
        }

    @mcp.resource(
        "tickets://stats",
        name="ticket_stats",
        description="Ticket counts by status, priority and product family.",
        mime_type="application/json",
    )
    def stats() -> dict:
        with session_scope() as s:
            return repo.ticket_stats(s)

    @mcp.resource(
        "tickets://recent",
        name="recent_tickets",
        description=f"The {RECENT_LIMIT} most recently registered tickets.",
        mime_type="application/json",
    )
    def recent() -> list[dict]:
        with session_scope() as s:
            return [TicketRead.from_model(t).model_dump(mode="json") for t in repo.recent_tickets(s, RECENT_LIMIT)]

    @mcp.resource(
        "tickets://{ticket_id}",
        name="ticket_by_id",
        description="A single ticket by ID, e.g. tickets://TKT-10001",
        mime_type="application/json",
    )
    def ticket_by_id(ticket_id: str) -> dict:
        try:
            with session_scope() as s:
                return TicketRead.from_model(repo.get_ticket(s, ticket_id)).model_dump(mode="json")
        except repo.TicketError as exc:
            raise ResourceError(str(exc)) from exc
