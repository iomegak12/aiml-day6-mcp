# ---------------------------------------------------------------
# IT Support Ticket MCP Server - developer shortcuts
# Works with GNU Make on Linux/macOS and Windows (cmd or Git Bash).
# ---------------------------------------------------------------

.DEFAULT_GOAL := help
.PHONY: help install run test clean docker-build up down logs seed reset-db inspector

SERVICE := ticket-mcp

# $(info) is printed by make itself (no shell), so it looks the same in cmd.exe and sh.
help: ## Show available targets
	$(info )
	$(info Usage: make <target>)
	$(info )
	$(info Development)
	$(info - make install        Install dependencies (uv sync))
	$(info - make run            Run the MCP server locally on port 8989)
	$(info - make test           Run the pytest suite)
	$(info - make clean          Remove __pycache__ and .pytest_cache)
	$(info )
	$(info Docker)
	$(info - make docker-build   Build the Docker image)
	$(info - make up             Build and start the container (detached))
	$(info - make down           Stop and remove the container)
	$(info - make logs           Follow container logs)
	$(info )
	$(info Utilities)
	$(info - make seed           Insert sample tickets (only when the DB is empty))
	$(info - make reset-db       Drop and recreate tables (empties the DB))
	$(info - make inspector      Launch MCP Inspector, then connect to http://localhost:8989/mcp)
	@echo Happy hacking!

# --- Development -------------------------------------------------------------
install:
	uv sync

run:
	uv run ticket-mcp

test:
	uv run pytest -v

clean:
	uv run python -c "import shutil, pathlib; dirs = [p for p in pathlib.Path('.').rglob('__pycache__') if '.venv' not in p.parts] + [pathlib.Path('.pytest_cache')]; [shutil.rmtree(d, ignore_errors=True) for d in dirs]; print('Cleaned', len(dirs), 'folders')"

# --- Docker ------------------------------------------------------------------
docker-build:
	docker compose build

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f $(SERVICE)

# --- Utilities ---------------------------------------------------------------
seed:
	uv run python -m ticket_mcp.seed

reset-db:
	uv run python -m ticket_mcp.seed --reset

inspector:
	npx -y @modelcontextprotocol/inspector
