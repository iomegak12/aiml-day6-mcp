"""MCP Prompts: reusable, parameterised prompt templates."""

import json
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import PromptError
from pydantic import Field

from ticket_mcp import repository as repo
from ticket_mcp.db import session_scope
from ticket_mcp.models import ProductFamily, Status, TicketRead


def register_prompts(mcp: FastMCP) -> None:
    @mcp.prompt(name="triage_ticket", tags={"tickets"})
    def triage_ticket(
        ticket_id: Annotated[str, Field(description="Ticket ID to triage, e.g. TKT-10001")],
    ) -> str:
        """Triage a ticket: assess priority, likely root cause and next steps."""
        try:
            with session_scope() as s:
                ticket = TicketRead.from_model(repo.get_ticket(s, ticket_id))
        except repo.TicketError as exc:
            raise PromptError(str(exc)) from exc

        return (
            "You are a senior network support engineer. Triage the IT support ticket below.\n\n"
            f"```json\n{ticket.model_dump_json(indent=2)}\n```\n\n"
            "Respond with:\n"
            "1. **Priority check** - is the current priority (P1 critical .. P4 low) appropriate? Why?\n"
            "2. **Likely root causes** - top 3, most likely first.\n"
            "3. **Diagnostic steps** - concrete commands/checks for this product family.\n"
            "4. **Recommended next action** - and whether the status should move to 'In Progress'.\n"
            "Keep it concise and actionable."
        )

    @mcp.prompt(name="summarize_open", tags={"tickets"})
    def summarize_open(
        product_family: Annotated[
            str | None,
            Field(description="Optional product family: " + ", ".join(f.value for f in ProductFamily)),
        ] = None,
    ) -> str:
        """Summarise all unresolved (Open / In Progress) tickets, optionally for one product family."""
        family: ProductFamily | None = None
        if product_family:
            match = next((f for f in ProductFamily if f.value.lower() == product_family.strip().lower()), None)
            if match is None:
                allowed = ", ".join(f.value for f in ProductFamily)
                raise PromptError(f"Unknown product family '{product_family}'. Allowed: {allowed}.")
            family = match

        items: list[dict] = []
        with session_scope() as s:
            for status in (Status.OPEN, Status.IN_PROGRESS):
                _, rows = repo.search_tickets(s, status=status, product_family=family, limit=repo.MAX_LIMIT)
                items.extend(TicketRead.from_model(t).model_dump(mode="json") for t in rows)

        scope = f"the '{family.value}' product family" if family else "all product families"
        if not items:
            return f"There are no Open or In Progress tickets for {scope}. Say so briefly."

        return (
            f"Summarise the following {len(items)} unresolved IT support tickets for {scope}.\n\n"
            f"```json\n{json.dumps(items, indent=2)}\n```\n\n"
            "Provide:\n"
            "1. A one-paragraph executive summary.\n"
            "2. A table grouped by priority (P1 first) with ticket ID, title, status and age.\n"
            "3. Common themes or recurring issues.\n"
            "4. The top 3 tickets to act on first, with a reason for each."
        )
