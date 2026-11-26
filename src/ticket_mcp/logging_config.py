"""Logging setup: colourful console output (rich) + optional rotating log file."""

import logging
from logging.handlers import RotatingFileHandler

from rich.logging import RichHandler

from ticket_mcp.config import Settings

FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging(settings: Settings) -> None:
    level = settings.log_level.upper()

    handlers: list[logging.Handler] = [
        RichHandler(rich_tracebacks=True, show_path=False, markup=False)
    ]

    file_handler: RotatingFileHandler | None = None
    if settings.log_to_file:
        settings.log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            settings.log_path,
            maxBytes=settings.log_max_bytes,
            backupCount=settings.log_backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(FILE_FORMAT))
        handlers.append(file_handler)

    logging.basicConfig(level=level, format="%(message)s", datefmt="[%X]", handlers=handlers, force=True)

    # FastMCP's logger does not propagate to root, so attach the file handler directly.
    if file_handler is not None:
        logging.getLogger("fastmcp").addHandler(file_handler)

    # Keep noisy third-party loggers quiet unless explicitly debugging.
    for noisy in ("sqlalchemy.engine", "docket"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # The MCP SDK logs a harmless ClosedResourceError when a client ends its session.
    logging.getLogger("mcp.server.streamable_http").addFilter(_ignore_closed_sse_writer)


def _ignore_closed_sse_writer(record: logging.LogRecord) -> bool:
    return "Error in standalone SSE writer" not in record.getMessage()
