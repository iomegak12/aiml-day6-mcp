"""Entrypoint: initialise DB, show banner, run Streamable HTTP server, shut down gracefully."""

import asyncio
import logging
import signal
import sys
from datetime import datetime

from rich.console import Console
from rich.panel import Panel

from ticket_mcp import db
from ticket_mcp.banner import show_banner
from ticket_mcp.config import Settings, get_settings
from ticket_mcp.logging_config import setup_logging
from ticket_mcp.seed import seed_if_empty
from ticket_mcp.server import create_server

logger = logging.getLogger("ticket_mcp")


def _install_sigterm_handler() -> None:
    """Treat SIGTERM (e.g. `docker stop`) like CTRL+C so both shut down the same way."""

    def _handler(signum: int, _frame) -> None:
        raise KeyboardInterrupt(f"signal {signum}")

    signal.signal(signal.SIGTERM, _handler)


async def _serve(settings: Settings, console: Console) -> None:
    db.init_engine(settings.database_url)
    db.create_tables()
    seeded = seed_if_empty() if settings.seed_data else 0
    if seeded:
        logger.info("Seeded %d sample tickets", seeded)

    mcp = create_server(settings.server_name)
    await show_banner(mcp, settings, seeded, console)

    await mcp.run_async(
        transport="http",
        host=settings.host,
        port=settings.port,
        path=settings.mcp_path,
        show_banner=False,  # we render our own banner
        uvicorn_config={
            "log_config": None,  # let uvicorn logs flow through our handlers
            "timeout_graceful_shutdown": 3,
        },
    )


def run() -> None:
    settings = get_settings()
    setup_logging(settings)
    _install_sigterm_handler()
    console = Console()
    started = datetime.now()

    exit_code = 0
    try:
        asyncio.run(_serve(settings, console))
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
    except SystemExit as exc:  # e.g. uvicorn failed to bind the port
        exit_code = exc.code if isinstance(exc.code, int) else 1
    except Exception:
        logger.exception("Server crashed")
        exit_code = 1
    finally:
        logger.info("Closing database connections")
        db.dispose_engine()
        uptime = str(datetime.now() - started).split(".")[0]
        status = "[bold green]Server stopped gracefully.[/]" if exit_code == 0 else "[bold red]Server stopped with errors.[/]"
        console.print(
            Panel(
                f"{status}  Uptime: [cyan]{uptime}[/]",
                border_style="green" if exit_code == 0 else "red",
                title="[bold]Goodbye[/]",
            )
        )
        logging.shutdown()

    sys.exit(exit_code)


if __name__ == "__main__":
    run()
