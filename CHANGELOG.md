# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-11-26

### Added

- FastMCP server using the Streamable HTTP transport on `0.0.0.0:8989` (`/mcp`), with no authentication.
- SQLite persistence through the SQLModel ORM. Ticket IDs are formatted as `TKT-10001`.
- Tools: `register_ticket`, `get_ticket`, `search_tickets`, `resolve_ticket`, `update_ticket_status`.
- Resources: `tickets://reference`, `tickets://stats`, `tickets://recent`, and the template `tickets://{ticket_id}`.
- Prompts: `triage_ticket`, `summarize_open`.
- Status lifecycle (Open → In Progress → Resolved → Closed), with reopen from Resolved.
- Colourful startup banner (rich + pyfiglet) and graceful shutdown on `CTRL+C` / `SIGTERM`.
- Rich console logging, plus rotating file logs in `logs/`.
- Sample data seeding and `/health` endpoint.
- `.env` configuration with a `.env.example` template.
- Dockerfile, `.dockerignore` and Docker Compose (named volumes, healthcheck).
- Makefile shortcuts, pytest suite, and project documentation.
