# syntax=docker/dockerfile:1
# ---------------------------------------------------------------
# IT Support Ticket MCP Server (FastMCP, Streamable HTTP)
# ---------------------------------------------------------------
FROM python:3.12-slim

# uv binary from the official image (pinned)
COPY --from=ghcr.io/astral-sh/uv:0.9.16 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# 1) Dependencies only (cached layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 2) Project source
COPY README.md LICENSE ./
COPY src ./src
RUN uv sync --frozen --no-dev

# 3) Non-root user + writable data/log folders
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data /app/logs \
    && chown -R appuser:appuser /app/data /app/logs
USER appuser

EXPOSE 8989

# Exec form so CTRL+C / SIGTERM reach Python directly (graceful shutdown)
CMD ["ticket-mcp"]
