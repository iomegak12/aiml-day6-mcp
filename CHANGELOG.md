# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `notebooks/ticket_agent_demo.ipynb`: a LangChain agent (OpenAI, `create_agent`) that uses the MCP server via `langchain-mcp-adapters` over Streamable HTTP. It has a help-desk system prompt and conversation memory (`InMemorySaver`), and demonstrates three use cases: help-desk intake, triage and resolve, and a manager status report.
- Agent dependencies: `langchain`, `langchain-openai`, `langchain-mcp-adapters`, `langgraph`, `ipykernel`, `python-dotenv`.
- `.env.example`: `OPENAI_API_KEY`, `AGENT_MODEL`, `MCP_SERVER_URL`.

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
