"""Exercise the MCP primitives through an in-memory FastMCP client."""

import json

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError


async def test_lists_all_primitives(mcp):
    async with Client(mcp) as c:
        tools = {t.name for t in await c.list_tools()}
        resources = {str(r.uri) for r in await c.list_resources()}
        templates = {t.uriTemplate for t in await c.list_resource_templates()}
        prompts = {p.name for p in await c.list_prompts()}

    assert tools == {"register_ticket", "get_ticket", "search_tickets", "resolve_ticket", "update_ticket_status"}
    assert resources == {"tickets://reference", "tickets://stats", "tickets://recent"}
    assert templates == {"tickets://{ticket_id}"}
    assert prompts == {"triage_ticket", "summarize_open"}


async def test_register_get_resolve_flow(mcp, new_ticket):
    async with Client(mcp) as c:
        created = (await c.call_tool("register_ticket", new_ticket)).structured_content
        tid = created["ticket_id"]
        assert tid == "TKT-10001" and created["status"] == "Open"
        assert created["ticket_date"].endswith("Z")

        fetched = (await c.call_tool("get_ticket", {"ticket_id": tid})).structured_content
        assert fetched["title"] == new_ticket["title"]

        resolved = (
            await c.call_tool("resolve_ticket", {"ticket_id": tid, "resolved_by": "Ravi", "remarks": "Rebooted"})
        ).structured_content
        assert resolved["status"] == "Resolved" and resolved["resolved_date"].endswith("Z")

        closed = (await c.call_tool("update_ticket_status", {"ticket_id": tid, "status": "Closed"})).structured_content
        assert closed["status"] == "Closed"


async def test_search_tool(mcp, new_ticket):
    async with Client(mcp) as c:
        await c.call_tool("register_ticket", new_ticket)
        await c.call_tool(
            "register_ticket",
            {**new_ticket, "title": "Firewall rule", "description": "Policy blocks app", "product_family": "Firewalls"},
        )
        result = (await c.call_tool("search_tickets", {"keyword": "ROUTER"})).structured_content
        assert result["total"] == 1 and result["items"][0]["product_family"] == "Routers"


async def test_tool_errors(mcp, new_ticket):
    async with Client(mcp) as c:
        with pytest.raises(ToolError, match="not found"):
            await c.call_tool("get_ticket", {"ticket_id": "TKT-10999"})
        tid = (await c.call_tool("register_ticket", new_ticket)).structured_content["ticket_id"]
        with pytest.raises(ToolError, match="Cannot move"):
            await c.call_tool("update_ticket_status", {"ticket_id": tid, "status": "Closed"})
        with pytest.raises(ToolError):
            await c.call_tool("register_ticket", {**new_ticket, "priority": "P9"})


async def test_resources(mcp, new_ticket):
    async with Client(mcp) as c:
        tid = (await c.call_tool("register_ticket", new_ticket)).structured_content["ticket_id"]

        ref = json.loads((await c.read_resource("tickets://reference"))[0].text)
        assert "SD-WAN" in ref["product_families"] and ref["priorities"] == ["P1", "P2", "P3", "P4"]

        stats = json.loads((await c.read_resource("tickets://stats"))[0].text)
        assert stats["total"] == 1 and stats["by_status"]["Open"] == 1

        recent = json.loads((await c.read_resource("tickets://recent"))[0].text)
        assert recent[0]["ticket_id"] == tid

        one = json.loads((await c.read_resource(f"tickets://{tid}"))[0].text)
        assert one["ticket_id"] == tid


async def test_prompts(mcp, new_ticket):
    async with Client(mcp) as c:
        tid = (await c.call_tool("register_ticket", new_ticket)).structured_content["ticket_id"]

        triage = await c.get_prompt("triage_ticket", {"ticket_id": tid})
        assert tid in triage.messages[0].content.text

        summary = await c.get_prompt("summarize_open", {"product_family": "routers"})
        assert "1 unresolved" in summary.messages[0].content.text
