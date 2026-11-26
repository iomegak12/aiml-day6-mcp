"""Database model (SQLModel) and data transfer objects."""

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel
from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, SQLModel

TICKET_PREFIX = "TKT-"
TICKET_OFFSET = 10000  # id 1 -> TKT-10001


class ProductFamily(str, Enum):
    ROUTERS = "Routers"
    SWITCHES = "Switches"
    SD_WAN = "SD-WAN"
    FIREWALLS = "Firewalls"
    OPTIC_CABLES = "Optic Cables"


class Priority(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class Status(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


def _enum_column(enum_cls: type[Enum], nullable: bool = False) -> Column:
    """Store enum *values* (e.g. 'SD-WAN') rather than member names in SQLite."""
    return Column(
        SAEnum(
            enum_cls,
            values_callable=lambda e: [m.value for m in e],
            native_enum=False,
            validate_strings=True,
        ),
        nullable=nullable,
        index=True,
    )


def utcnow() -> datetime:
    """Current time as a timezone-aware UTC datetime (seconds precision)."""
    return datetime.now(timezone.utc).replace(microsecond=0)


def to_iso(value: datetime | None) -> str | None:
    """Format a datetime as UTC ISO 8601 with a 'Z' suffix, e.g. 2026-11-26T10:15:00Z."""
    if value is None:
        return None
    if value.tzinfo is None:  # treat naive values as UTC
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def format_ticket_id(pk: int) -> str:
    return f"{TICKET_PREFIX}{TICKET_OFFSET + pk}"


class Ticket(SQLModel, table=True):
    __tablename__ = "tickets"

    id: int | None = Field(default=None, primary_key=True)
    ticket_date: datetime = Field(default_factory=utcnow, index=True)
    registered_by: str = Field(index=True, max_length=100)
    title: str = Field(max_length=200)
    description: str
    product_family: ProductFamily = Field(sa_column=_enum_column(ProductFamily))
    priority: Priority = Field(sa_column=_enum_column(Priority))
    status: Status = Field(default=Status.OPEN, sa_column=_enum_column(Status))
    resolved_by: str | None = Field(default=None, index=True, max_length=100)
    resolved_date: datetime | None = None
    remarks: str | None = None

    @property
    def ticket_id(self) -> str:
        return format_ticket_id(self.id or 0)


class TicketRead(BaseModel):
    """Public representation of a ticket returned by tools and resources."""

    ticket_id: str
    ticket_date: str
    registered_by: str
    title: str
    description: str
    product_family: ProductFamily
    priority: Priority
    status: Status
    resolved_by: str | None = None
    resolved_date: str | None = None
    remarks: str | None = None

    @classmethod
    def from_model(cls, t: Ticket) -> "TicketRead":
        return cls(
            ticket_id=t.ticket_id,
            ticket_date=to_iso(t.ticket_date) or "",
            registered_by=t.registered_by,
            title=t.title,
            description=t.description,
            product_family=t.product_family,
            priority=t.priority,
            status=t.status,
            resolved_by=t.resolved_by,
            resolved_date=to_iso(t.resolved_date),
            remarks=t.remarks,
        )


class SearchResult(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[TicketRead]
