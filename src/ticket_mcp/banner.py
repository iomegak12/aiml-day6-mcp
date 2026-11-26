"""Colourful startup banner shown in the console."""

import platform

import fastmcp
import pyfiglet
from fastmcp import FastMCP
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ticket_mcp import __version__
from ticket_mcp.config import Settings

GRADIENT = ["#00d7ff", "#00afff", "#5f87ff", "#875fff", "#af5fff", "#d75fff"]


def _gradient_ascii(text: str) -> Text:
    art = pyfiglet.figlet_format(text, font="slant").rstrip("\n")
    out = Text()
    for i, line in enumerate(art.splitlines()):
        out.append(line + "\n", style=f"bold {GRADIENT[i % len(GRADIENT)]}")
    return out


async def show_banner(mcp: FastMCP, settings: Settings, seeded: int, console: Console | None = None) -> None:
    console = console or Console()

    tools = await mcp.get_tools()
    resources = await mcp.get_resources()
    templates = await mcp.get_resource_templates()
    prompts = await mcp.get_prompts()

    display_host = "localhost" if settings.host in ("0.0.0.0", "::") else settings.host
    base_url = f"http://{display_host}:{settings.port}"

    info = Table.grid(padding=(0, 2))
    info.add_column(style="bold cyan", justify="right")
    info.add_column(style="white")
    info.add_row("Server", f"[bold]{settings.server_name}[/] v{__version__}")
    info.add_row("Transport", "[green]Streamable HTTP[/]")
    info.add_row("Host", f"[yellow]{settings.host}[/]")
    info.add_row("Port", f"[yellow]{settings.port}[/]")
    info.add_row("MCP Endpoint", f"[link={base_url}{settings.mcp_path}]{base_url}{settings.mcp_path}[/]")
    info.add_row("Health Check", f"{base_url}/health")
    info.add_row("Authentication", "[magenta]None[/]")
    info.add_row("Database", str(settings.database_url))
    info.add_row("Seed Data", f"{'enabled' if settings.seed_data else 'disabled'} ({seeded} inserted)")
    info.add_row("Log Level", settings.log_level.upper())
    info.add_row("Log File", str(settings.log_path) if settings.log_to_file else "[dim]disabled[/]")
    info.add_row("Runtime", f"Python {platform.python_version()} | FastMCP {fastmcp.__version__}")

    prim = Table(title="MCP Primitives", title_style="bold magenta", show_lines=False, expand=True)
    prim.add_column("Type", style="bold green", no_wrap=True)
    prim.add_column("Count", justify="center", style="bold yellow")
    prim.add_column("Names", style="white")
    prim.add_row("Tools", str(len(tools)), ", ".join(sorted(tools)))
    prim.add_row("Resources", str(len(resources)), ", ".join(sorted(resources)))
    prim.add_row("Templates", str(len(templates)), ", ".join(sorted(templates)))
    prim.add_row("Prompts", str(len(prompts)), ", ".join(sorted(prompts)))

    console.print(Align.center(_gradient_ascii("Ticket MCP")))
    console.print(
        Panel(
            Group(info, Text(""), prim),
            title="[bold white on blue] IT Support Ticket MCP Server [/]",
            subtitle="[dim]Press CTRL+C to stop[/]",
            border_style="bright_blue",
            padding=(1, 2),
        )
    )
