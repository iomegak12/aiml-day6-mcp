"""MCP Tools: actions the model can invoke."""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from ticket_mcp import repository as repo
from ticket_mcp.db import session_scope
from ticket_mcp.models import Priority, ProductFamily, SearchResult, Status, TicketRead

logger = logging.getLogger(__name__)

TicketId = Annotated[str, Field(description="Ticket ID, e.g. TKT-10001")]


@contextmanager
def _as_tool_error() -> Iterator[None]:
    """Turn domain errors into ToolError so the client gets a clean error message."""
    try:
        yield
    except repo.TicketError as exc:
        raise ToolError(str(exc)) from exc


def register_tools(mcp: FastMCP) -> None:
    @mcp.tool(tags={"tickets", "write"})
    def register_ticket(
        title: Annotated[str, Field(description="Short summary of the issue", min_length=3, max_length=200)],
        description: Annotated[str, Field(description="Detailed description of the issue", min_length=3)],
        product_family: Annotated[ProductFamily, Field(description="Affected product family")],
        priority: Annotated[Priority, Field(description="P1 (critical) .. P4 (low)")],
        registered_by: Annotated[str, Field(description="Name of the person registering the ticket")],
    ) -> TicketRead:
        """Register a new IT support ticket. The ticket starts in 'Open' status."""
        with _as_tool_error(), session_scope() as s:
            ticket = repo.register_ticket(
                s,
                title=title,
                description=description,
                product_family=product_family,
                priority=priority,
                registered_by=registered_by,
            )
            logger.info("Registered %s (%s, %s)", ticket.ticket_id, priority.value, product_family.value)
            return TicketRead.from_model(ticket)

    @mcp.tool(tags={"tickets", "read"}, annotations={"readOnlyHint": True})
    def get_ticket(ticket_id: TicketId) -> TicketRead:
        """Get full details of a ticket by its ID."""
        with _as_tool_error(), session_scope() as s:
            return TicketRead.from_model(repo.get_ticket(s, ticket_id))

    @mcp.tool(tags={"tickets", "read"}, annotations={"readOnlyHint": True})
    def search_tickets(
        status: Annotated[Status | None, Field(description="Filter by status")] = None,
        priority: Annotated[Priority | None, Field(description="Filter by priority")] = None,
        product_family: Annotated[ProductFamily | None, Field(description="Filter by product family")] = None,
        keyword: Annotated[str | None, Field(description="Partial, case-insensitive match on title/description")] = None,
        registered_by: Annotated[str | None, Field(description="Partial, case-insensitive match")] = None,
        resolved_by: Annotated[str | None, Field(description="Partial, case-insensitive match")] = None,
        date_from: Annotated[str | None, Field(description="Ticket date from (ISO 8601), e.g. 2026-11-01")] = None,
        date_to: Annotated[str | None, Field(description="Ticket date to (ISO 8601, inclusive)")] = None,
        limit: Annotated[int, Field(ge=1, le=repo.MAX_LIMIT, description="Page size")] = 20,
        offset: Annotated[int, Field(ge=0, description="Number of results to skip")] = 0,
    ) -> SearchResult:
        """Search tickets. All filters are optional and combinable. Newest tickets first."""
        with _as_tool_error(), session_scope() as s:
            total, rows = repo.search_tickets(
                s,
                status=status,
                priority=priority,
                product_family=product_family,
                keyword=keyword,
                registered_by=registered_by,
                resolved_by=resolved_by,
                date_from=date_from,
                date_to=date_to,
                limit=limit,
                offset=offset,
            )
            return SearchResult(
                total=total,
                limit=limit,
                offset=offset,
                items=[TicketRead.from_model(t) for t in rows],
            )

    @mcp.tool(tags={"tickets", "write"})
    def resolve_ticket(
        ticket_id: TicketId,
        resolved_by: Annotated[str, Field(description="Name of the person who resolved the ticket")],
        remarks: Annotated[str, Field(description="Resolution notes", min_length=3)],
    ) -> TicketRead:
        """Resolve a ticket that is 'Open' or 'In Progress'. Resolved date is set automatically (UTC)."""
        with _as_tool_error(), session_scope() as s:
            ticket = repo.resolve_ticket(s, ticket_id, resolved_by=resolved_by, remarks=remarks)
            logger.info("Resolved %s by %s", ticket.ticket_id, resolved_by)
            return TicketRead.from_model(ticket)

    @mcp.tool(tags={"tickets", "write"})
    def update_ticket_status(
        ticket_id: TicketId,
        status: Annotated[Status, Field(description="New status: 'In Progress', 'Closed' or 'Open' (reopen)")],
        remarks: Annotated[str | None, Field(description="Optional note recorded in remarks")] = None,
    ) -> TicketRead:
        """Move a ticket through its lifecycle.

        Allowed: Open -> In Progress, Resolved -> Closed, Resolved -> Open (reopen).
        Use 'resolve_ticket' to resolve a ticket.
        """
        with _as_tool_error(), session_scope() as s:
            ticket = repo.update_ticket_status(s, ticket_id, status=status, remarks=remarks)
            logger.info("Status of %s -> %s", ticket.ticket_id, status.value)
            return TicketRead.from_model(ticket)
