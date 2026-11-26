"""Sample data for demos.

Run directly:
    uv run python -m ticket_mcp.seed            # seed if the DB is empty
    uv run python -m ticket_mcp.seed --reset    # drop & recreate tables (empty DB)
"""

import argparse
import logging
from datetime import timedelta

from ticket_mcp import db
from ticket_mcp.config import get_settings
from ticket_mcp.models import Priority as P
from ticket_mcp.models import ProductFamily as F
from ticket_mcp.models import Status as S
from ticket_mcp.models import Ticket, utcnow
from ticket_mcp.repository import count_tickets

logger = logging.getLogger(__name__)

# (days_ago, registered_by, title, description, family, priority, status, resolved_by, resolved_days_ago, remarks)
SAMPLE_TICKETS = [
    (30, "Anita Sharma", "Core router BGP session flapping", "BGP peer with ISP-A drops every 10 minutes on CR-01.", F.ROUTERS, P.P1, S.CLOSED, "Vikram Rao", 29, "Hold timer mismatch fixed; MD5 key re-synced."),
    (28, "John Mathew", "Branch switch port errors", "CRC errors on Gi1/0/24 at Pune branch access switch.", F.SWITCHES, P.P3, S.RESOLVED, "Priya Nair", 27, "Replaced faulty patch cord."),
    (26, "Meera Iyer", "SD-WAN tunnel down at Chennai", "Overlay tunnel to hub shows down; underlay is reachable.", F.SD_WAN, P.P1, S.RESOLVED, "Karthik S", 25, "Expired certificate renewed on edge device."),
    (24, "Rahul Verma", "Firewall blocking payroll app", "Users cannot reach payroll.example.com since policy push.", F.FIREWALLS, P.P2, S.CLOSED, "Vikram Rao", 24, "Added missing FQDN object to allow rule."),
    (22, "Sneha Kulkarni", "Fiber link high attenuation", "OTDR shows 6 dB loss on DC-A to DC-B link.", F.OPTIC_CABLES, P.P2, S.RESOLVED, "Arjun Menon", 20, "Re-spliced connector at patch panel 3."),
    (20, "Anita Sharma", "Router CPU spikes at 95%", "Edge router ER-02 CPU high during business hours.", F.ROUTERS, P.P2, S.IN_PROGRESS, None, None, None),
    (18, "David Fernandes", "VLAN not propagating", "New VLAN 230 missing on distribution switches.", F.SWITCHES, P.P3, S.OPEN, None, None, None),
    (16, "Meera Iyer", "SD-WAN policy routing wrong path", "Voice traffic going over broadband instead of MPLS.", F.SD_WAN, P.P2, S.IN_PROGRESS, None, None, None),
    (14, "Rahul Verma", "Firewall HA failover test", "Schedule and validate HA failover for FW cluster.", F.FIREWALLS, P.P4, S.OPEN, None, None, None),
    (12, "Sneha Kulkarni", "Damaged optic cable in tray", "Cable tray work damaged 2 fiber runs in floor 4.", F.OPTIC_CABLES, P.P1, S.IN_PROGRESS, None, None, None),
    (10, "John Mathew", "Switch stack member offline", "Member 3 in stack SW-STK-02 not responding.", F.SWITCHES, P.P1, S.RESOLVED, "Priya Nair", 9, "Reseated stack cable; member rejoined."),
    (8, "Kavya Reddy", "Router firmware upgrade request", "Upgrade branch routers to latest stable firmware.", F.ROUTERS, P.P4, S.OPEN, None, None, None),
    (7, "David Fernandes", "Firewall VPN users disconnecting", "Remote VPN users disconnect after ~30 minutes.", F.FIREWALLS, P.P2, S.OPEN, None, None, None),
    (5, "Kavya Reddy", "SD-WAN edge onboarding failure", "New edge at Kochi stuck in 'staging' state.", F.SD_WAN, P.P3, S.OPEN, None, None, None),
    (4, "Anita Sharma", "Spanning tree topology changes", "Frequent TCNs logged on core switch.", F.SWITCHES, P.P2, S.IN_PROGRESS, None, None, None),
    (3, "Meera Iyer", "Optic transceiver not detected", "SFP+ module in slot 2/1 shows 'unsupported'.", F.OPTIC_CABLES, P.P3, S.OPEN, None, None, None),
    (2, "Rahul Verma", "Firewall log storage full", "Log partition at 98%; logs being dropped.", F.FIREWALLS, P.P1, S.OPEN, None, None, None),
    (1, "John Mathew", "Router interface flapping", "Gi0/0/1 on BR-RTR-07 flapping since morning.", F.ROUTERS, P.P2, S.OPEN, None, None, None),
]


def seed_if_empty() -> int:
    """Insert sample tickets when the table is empty. Returns number inserted."""
    with db.session_scope() as session:
        if count_tickets(session) > 0:
            return 0
        now = utcnow()
        for days, reg_by, title, desc, fam, pri, status, res_by, res_days, remarks in SAMPLE_TICKETS:
            session.add(
                Ticket(
                    ticket_date=now - timedelta(days=days, hours=days % 7),
                    registered_by=reg_by,
                    title=title,
                    description=desc,
                    product_family=fam,
                    priority=pri,
                    status=status,
                    resolved_by=res_by,
                    resolved_date=(now - timedelta(days=res_days)) if res_days is not None else None,
                    remarks=remarks,
                )
            )
        return len(SAMPLE_TICKETS)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed or reset the ticket database.")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables (empty DB).")
    args = parser.parse_args()

    settings = get_settings()
    db.init_engine(settings.database_url)
    try:
        if args.reset:
            db.drop_tables()
            db.create_tables()
            print(f"Database reset: {settings.database_url}")
        else:
            db.create_tables()
            inserted = seed_if_empty()
            print(f"Inserted {inserted} sample tickets." if inserted else "Database already has tickets; nothing seeded.")
    finally:
        db.dispose_engine()


if __name__ == "__main__":
    main()
