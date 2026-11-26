"""FastMCP server definition: wires tools, resources, prompts and a health route."""

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from ticket_mcp import __version__, db
from ticket_mcp.prompts import register_prompts
from ticket_mcp.resources import register_resources
from ticket_mcp.tools import register_tools

INSTRUCTIONS = """\
IT Support Ticket server. Use it to register, look up, search, resolve and
update the status of IT support tickets (IDs look like TKT-10001).
Product families: Routers, Switches, SD-WAN, Firewalls, Optic Cables.
Priorities: P1 (critical) .. P4 (low). Statuses: Open, In Progress, Resolved, Closed.
Read the 'tickets://reference' resource for allowed values and status transitions.
"""


def create_server(name: str) -> FastMCP:
    mcp = FastMCP(name=name, instructions=INSTRUCTIONS, version=__version__)

    register_tools(mcp)
    register_resources(mcp)
    register_prompts(mcp)

    @mcp.custom_route("/health", methods=["GET"])
    async def health(_: Request) -> JSONResponse:
        healthy = db.ping()
        return JSONResponse(
            {"status": "ok" if healthy else "degraded", "database": healthy, "version": __version__},
            status_code=200 if healthy else 503,
        )

    return mcp
