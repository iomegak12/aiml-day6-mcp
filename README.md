# IT Support Ticket MCP Server

An [MCP](https://modelcontextprotocol.io) server built with **FastMCP** (Python) for tracking IT support tickets in SQLite. It demonstrates all three MCP primitives (**Tools**, **Resources** and **Prompts**) over **Streamable HTTP**.

## Features

- Register, get, search, resolve and update the status of IT support tickets
- SQLite storage through the **SQLModel** ORM
- Streamable HTTP transport on `0.0.0.0:8989` at the `/mcp` path, with no authentication
- A colourful startup banner (rich + pyfiglet)
- Graceful shutdown on `CTRL+C` / `SIGTERM`
- Rotating file logs in `logs/`
- Sample tickets seeded automatically on first start
- Runs in Docker via Dockerfile and Docker Compose, with a healthcheck

## Ticket model

| Field | Notes |
|---|---|
| Ticket ID | `TKT-10001`, `TKT-10002`, … (auto-generated) |
| Ticket Date | UTC ISO 8601, e.g. `2026-11-26T10:15:00Z` (auto) |
| Registered By | Free text |
| Title / Description | Free text |
| Product Family | `Routers`, `Switches`, `SD-WAN`, `Firewalls`, `Optic Cables` |
| Priority | `P1` (critical) to `P4` (low) |
| Status | `Open`, `In Progress`, `Resolved`, `Closed` |
| Resolved By / Resolved Date | Set when the ticket is resolved |
| Remarks | Timestamped history of status notes |

**Status transitions**

| From | Allowed next status |
|---|---|
| Open | In Progress, Resolved |
| In Progress | Resolved |
| Resolved | Closed, Open (reopen) |
| Closed | none (final state) |

## MCP primitives

| Type | Name | Description |
|---|---|---|
| Tool | `register_ticket` | Create a ticket (status `Open`) |
| Tool | `get_ticket` | Get a ticket by ID |
| Tool | `search_tickets` | Filter by status, priority, product family, keyword, registered/resolved by, or date range. Supports `limit`/`offset`. |
| Tool | `resolve_ticket` | Resolve with `resolved_by` + `remarks`. The resolved date is set automatically. |
| Tool | `update_ticket_status` | Move to `In Progress`, `Closed`, or reopen to `Open` |
| Resource | `tickets://reference` | Allowed values and status transitions |
| Resource | `tickets://stats` | Counts by status, priority and product family |
| Resource | `tickets://recent` | The 10 most recent tickets |
| Resource template | `tickets://{ticket_id}` | A single ticket |
| Prompt | `triage_ticket` | Triage a ticket: priority check, root causes, next steps |
| Prompt | `summarize_open` | Summarise unresolved tickets, optionally for one product family |

## Quick start

**Prerequisites:** Python 3.12 and [uv](https://docs.astral.sh/uv/). Optional: Docker, GNU Make, Node.js (for MCP Inspector).

```bash
cp .env.example .env      # Windows PowerShell: Copy-Item .env.example .env
```

### With uv

```bash
uv sync
uv run ticket-mcp
```

### With make

```bash
make install
make run
```

### With Docker

```bash
docker compose up -d --build     # or: make up
docker compose logs -f           # or: make logs
docker compose down              # or: make down
```

The server listens at **http://localhost:8989/mcp**. The health check is at http://localhost:8989/health.

### Try it with MCP Inspector

```bash
npx -y @modelcontextprotocol/inspector     # or: make inspector
```

Select the **Streamable HTTP** transport, enter the URL `http://localhost:8989/mcp`, and click **Connect**.

### Use it from Claude Code / Claude Desktop

```bash
claude mcp add --transport http tickets http://localhost:8989/mcp
```

## Make targets

| Target | Description |
|---|---|
| `make install` | `uv sync` |
| `make run` | Run the server locally |
| `make test` | Run pytest |
| `make clean` | Remove caches |
| `make docker-build` / `up` / `down` / `logs` | Docker Compose helpers |
| `make seed` | Insert sample tickets if the DB is empty |
| `make reset-db` | Drop and recreate tables (empties the DB) |
| `make inspector` | Launch MCP Inspector |

### Installing `make` on Windows

Use any one of these:

```powershell
winget install ezwinports.make
choco install make
scoop install make
```

Or use **Git Bash**, which can run `make` once it is installed by one of the options above.

## Configuration (`.env`)

| Variable | Default | Description |
|---|---|---|
| `SERVER_NAME` | `IT Support Ticket MCP Server` | Display name |
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8989` | Port |
| `MCP_PATH` | `/mcp` | Streamable HTTP endpoint path |
| `DATABASE_URL` | `sqlite:///./data/tickets.db` | SQLAlchemy URL |
| `SEED_DATA` | `true` | Seed sample tickets when the DB is empty |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL` |
| `LOG_TO_FILE` | `true` | Enable rotating file logs |
| `LOG_DIR` / `LOG_FILE` | `./logs` / `ticket-mcp.log` | Log file location |
| `LOG_MAX_BYTES` / `LOG_BACKUP_COUNT` | `1048576` / `5` | Rotation settings |

## Project structure

```
src/ticket_mcp/
├── config.py          # Settings from .env (pydantic-settings)
├── logging_config.py  # Rich console + rotating file logs
├── db.py              # Engine, sessions, table creation
├── models.py          # SQLModel Ticket table, enums, DTOs
├── repository.py      # Business rules & queries (no MCP code)
├── seed.py            # Sample data + CLI (seed / reset)
├── tools.py           # MCP tools
├── resources.py       # MCP resources
├── prompts.py         # MCP prompts
├── server.py          # FastMCP instance + /health route
├── banner.py          # Startup banner
└── main.py            # Entrypoint & graceful shutdown
tests/                 # pytest (repository + in-memory MCP client)
data/  logs/           # Runtime folders (kept via .gitkeep)
```

## Documentation

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [CHANGELOG.md](CHANGELOG.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [SECURITY.md](SECURITY.md)

## License

[MIT](LICENSE) © 2026 Ramkumar
