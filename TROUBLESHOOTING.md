# Troubleshooting

## Port 8989 is already in use

Symptom: `[Errno 98] address already in use` or `[WinError 10048]`.

```powershell
# Windows: find and stop the process
Get-NetTCPConnection -LocalPort 8989 | Select-Object OwningProcess
Stop-Process -Id <PID>
```

```bash
# Linux/macOS
lsof -i :8989
kill <PID>
```

Or change `PORT` in `.env`. The container may also still be running: `make down`.

## `make` is not recognised (Windows)

Install GNU Make with `winget install ezwinports.make`, `choco install make` or `scoop install make`, then reopen the terminal. You can also skip make and run the underlying commands directly, for example `uv run ticket-mcp`.

## `uv` is not recognised

Install uv: <https://docs.astral.sh/uv/getting-started/installation/>, then reopen the terminal.

## MCP Inspector can't connect

- Choose the **Streamable HTTP** transport, not SSE or STDIO.
- The URL must include the path: `http://localhost:8989/mcp`.
- Check that the server is up: open http://localhost:8989/health.
- On Windows, if `0.0.0.0` causes trouble, connect to `localhost` or `127.0.0.1`.

## Database is locked, or I want a fresh DB

Stop every running server instance (local **and** Docker), then run:

```bash
make reset-db   # empty tables
make seed       # optional: sample tickets
```

For Docker, remove the volume: `docker compose down -v`.

## No sample tickets appear

Seeding only runs when `SEED_DATA=true` **and** the DB is empty. Run `make reset-db`, then `make seed`.

## Docker: permission denied on `/app/data` or `/app/logs`

The container runs as a non-root user (UID 10001). If you replaced the named volumes with bind mounts, make the host folders writable, or switch back to the named volumes in `docker-compose.yml`.

## Docker: no colours in logs

`tty: true` is set in `docker-compose.yml`. Colours appear with `docker compose logs`, but not when output is piped to a file.

## CTRL+C doesn't stop the server immediately

Open client sessions are given up to 3 seconds to close. Press CTRL+C a second time to force the server to stop. In Docker, `docker compose stop` sends SIGINT and waits up to 15 seconds.

## Tool error: "Cannot move TKT-… from 'X' to 'Y'"

The status transition isn't allowed. Read the `tickets://reference` resource for the allowed transitions, and use `resolve_ticket` (not `update_ticket_status`) to resolve.

## Where are the logs?

- Console: coloured output.
- File: `logs/ticket-mcp.log`, rotated at 1 MB with 5 backups. In Docker it's in the `ticket-logs` volume.
- Set `LOG_LEVEL=DEBUG` in `.env` for more detail.
