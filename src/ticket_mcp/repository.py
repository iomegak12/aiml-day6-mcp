"""Data-access and business rules for tickets (no MCP specifics in here)."""

import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_
from sqlmodel import Session, col, select

from ticket_mcp.models import (
    TICKET_OFFSET,
    Priority,
    ProductFamily,
    Status,
    Ticket,
    to_iso,
    utcnow,
)

MAX_LIMIT = 100

# Allowed status transitions (strict forward, plus reopen from Resolved).
ALLOWED_TRANSITIONS: dict[Status, set[Status]] = {
    Status.OPEN: {Status.IN_PROGRESS, Status.RESOLVED},
    Status.IN_PROGRESS: {Status.RESOLVED},
    Status.RESOLVED: {Status.CLOSED, Status.OPEN},
    Status.CLOSED: set(),
}

_TICKET_ID_RE = re.compile(r"^\s*(?:TKT-)?(\d+)\s*$", re.IGNORECASE)


# --- Errors -----------------------------------------------------------------
class TicketError(Exception):
    """Base class for ticket domain errors."""


class TicketNotFoundError(TicketError):
    pass


class InvalidTicketIdError(TicketError):
    pass


class InvalidTransitionError(TicketError):
    pass


class InvalidInputError(TicketError):
    pass


# --- Helpers ----------------------------------------------------------------
def parse_ticket_id(ticket_id: str) -> int:
    """'TKT-10001' (or '10001') -> primary key 1."""
    match = _TICKET_ID_RE.match(ticket_id or "")
    if not match:
        raise InvalidTicketIdError(f"Invalid ticket id '{ticket_id}'. Expected format TKT-10001.")
    pk = int(match.group(1)) - TICKET_OFFSET
    if pk < 1:
        raise InvalidTicketIdError(f"Invalid ticket id '{ticket_id}'. Ticket numbers start at TKT-10001.")
    return pk


def parse_iso_datetime(value: str, *, end_of_day: bool = False) -> datetime:
    """Parse an ISO date/datetime into aware UTC (naive input = UTC). Date-only covers the whole day."""
    try:
        parsed = datetime.fromisoformat(value.strip())
    except ValueError as exc:
        raise InvalidInputError(
            f"Invalid date '{value}'. Use ISO 8601, e.g. 2026-11-26 or 2026-11-26T10:00:00Z."
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    if end_of_day and len(value.strip()) == 10:  # date-only -> inclusive end of day
        parsed = parsed + timedelta(days=1) - timedelta(microseconds=1)
    return parsed


def _append_remark(ticket: Ticket, text: str | None, label: str) -> None:
    if not text or not text.strip():
        return
    entry = f"[{to_iso(utcnow())}] {label}: {text.strip()}"
    ticket.remarks = f"{ticket.remarks}\n{entry}" if ticket.remarks else entry


def _require(value: str, field: str) -> str:
    if not value or not value.strip():
        raise InvalidInputError(f"'{field}' must not be empty.")
    return value.strip()


# --- Operations -------------------------------------------------------------
def register_ticket(
    session: Session,
    *,
    title: str,
    description: str,
    product_family: ProductFamily,
    priority: Priority,
    registered_by: str,
) -> Ticket:
    ticket = Ticket(
        title=_require(title, "title"),
        description=_require(description, "description"),
        product_family=product_family,
        priority=priority,
        registered_by=_require(registered_by, "registered_by"),
        status=Status.OPEN,
        ticket_date=utcnow(),
    )
    session.add(ticket)
    session.flush()
    session.refresh(ticket)
    return ticket


def get_ticket(session: Session, ticket_id: str) -> Ticket:
    ticket = session.get(Ticket, parse_ticket_id(ticket_id))
    if ticket is None:
        raise TicketNotFoundError(f"Ticket '{ticket_id}' was not found.")
    return ticket


def search_tickets(
    session: Session,
    *,
    status: Status | None = None,
    priority: Priority | None = None,
    product_family: ProductFamily | None = None,
    keyword: str | None = None,
    registered_by: str | None = None,
    resolved_by: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[int, list[Ticket]]:
    """Combinable filters. Text filters are case-insensitive partial matches."""
    conditions = []
    if status:
        conditions.append(col(Ticket.status) == status)
    if priority:
        conditions.append(col(Ticket.priority) == priority)
    if product_family:
        conditions.append(col(Ticket.product_family) == product_family)
    if keyword and keyword.strip():
        pattern = f"%{keyword.strip()}%"
        conditions.append(or_(col(Ticket.title).ilike(pattern), col(Ticket.description).ilike(pattern)))
    if registered_by and registered_by.strip():
        conditions.append(col(Ticket.registered_by).ilike(f"%{registered_by.strip()}%"))
    if resolved_by and resolved_by.strip():
        conditions.append(col(Ticket.resolved_by).ilike(f"%{resolved_by.strip()}%"))
    if date_from:
        conditions.append(col(Ticket.ticket_date) >= parse_iso_datetime(date_from))
    if date_to:
        conditions.append(col(Ticket.ticket_date) <= parse_iso_datetime(date_to, end_of_day=True))

    limit = max(1, min(limit, MAX_LIMIT))
    offset = max(0, offset)

    total = session.exec(select(func.count()).select_from(Ticket).where(*conditions)).one()
    rows = session.exec(
        select(Ticket)
        .where(*conditions)
        .order_by(col(Ticket.ticket_date).desc(), col(Ticket.id).desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return total, list(rows)


def _check_transition(ticket: Ticket, target: Status) -> None:
    if target not in ALLOWED_TRANSITIONS[ticket.status]:
        allowed = ", ".join(s.value for s in ALLOWED_TRANSITIONS[ticket.status]) or "none (final state)"
        raise InvalidTransitionError(
            f"Cannot move {ticket.ticket_id} from '{ticket.status.value}' to '{target.value}'. "
            f"Allowed next status: {allowed}."
        )


def resolve_ticket(session: Session, ticket_id: str, *, resolved_by: str, remarks: str) -> Ticket:
    ticket = get_ticket(session, ticket_id)
    _check_transition(ticket, Status.RESOLVED)
    ticket.resolved_by = _require(resolved_by, "resolved_by")
    remarks = _require(remarks, "remarks")
    ticket.status = Status.RESOLVED
    ticket.resolved_date = utcnow()
    _append_remark(ticket, remarks, f"Resolved by {ticket.resolved_by}")
    session.add(ticket)
    session.flush()
    return ticket


def update_ticket_status(
    session: Session, ticket_id: str, *, status: Status, remarks: str | None = None
) -> Ticket:
    if status == Status.RESOLVED:
        raise InvalidTransitionError("Use the 'resolve_ticket' tool to resolve a ticket.")
    ticket = get_ticket(session, ticket_id)
    _check_transition(ticket, status)

    if status == Status.OPEN:  # reopen: clear the previous resolution
        ticket.resolved_by = None
        ticket.resolved_date = None

    ticket.status = status
    _append_remark(ticket, remarks, status.value)
    session.add(ticket)
    session.flush()
    return ticket


def recent_tickets(session: Session, limit: int = 10) -> list[Ticket]:
    _, rows = search_tickets(session, limit=limit)
    return rows


def ticket_stats(session: Session) -> dict:
    def counts(column, enum_cls) -> dict[str, int]:
        rows = session.exec(select(column, func.count()).group_by(column)).all()
        found = {(k.value if hasattr(k, "value") else k): v for k, v in rows}
        return {m.value: found.get(m.value, 0) for m in enum_cls}

    total = session.exec(select(func.count()).select_from(Ticket)).one()
    return {
        "total": total,
        "by_status": counts(col(Ticket.status), Status),
        "by_priority": counts(col(Ticket.priority), Priority),
        "by_product_family": counts(col(Ticket.product_family), ProductFamily),
    }


def count_tickets(session: Session) -> int:
    return session.exec(select(func.count()).select_from(Ticket)).one()
