# Contributing

Thanks for your interest in improving this project! Everyone taking part is expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Development setup

```bash
git clone <repo-url> && cd mcp-practices
cp .env.example .env
uv sync            # or: make install
uv run ticket-mcp  # or: make run
```

You need Python 3.12 and [uv](https://docs.astral.sh/uv/). GNU Make, Docker and Node.js (for MCP Inspector) are optional.

## Where things go

| Change | File |
|---|---|
| New field or enum value | `src/ticket_mcp/models.py` (and the seed data) |
| Business rules and queries | `src/ticket_mcp/repository.py` |
| New MCP tool, resource or prompt | `tools.py` / `resources.py` / `prompts.py` |
| New setting | `config.py` **and** `.env.example` **and** the README config table |

Keep MCP-specific code out of `repository.py`. That way the rules can be tested without a client.

## Branches and commits

- Branch from `main` with a name like `feat/…`, `fix/…` or `docs/…`.
- Use [Conventional Commits](https://www.conventionalcommits.org/), for example:
  - `feat: add assign_ticket tool`
  - `fix: reject empty remarks on resolve`
  - `docs: clarify docker volume usage`

## Tests

```bash
uv run pytest -v   # or: make test
```

- Add tests for every new tool, resource, prompt or rule.
- `tests/test_repository.py` covers business rules. `tests/test_mcp_server.py` goes through the in-memory FastMCP `Client`.

## Pull request checklist

- [ ] Tests added or updated, and `make test` passes
- [ ] The server starts (`make run`) and works in MCP Inspector
- [ ] `docker compose up --build` still works, if Docker files changed
- [ ] `.env.example` and the README are updated for any new setting
- [ ] Entry added under `[Unreleased]` in [CHANGELOG.md](CHANGELOG.md)

## Reporting bugs and ideas

Open an issue that includes steps to reproduce, the expected result, the actual result, and relevant log lines from `logs/ticket-mcp.log`. For security issues, follow [SECURITY.md](SECURITY.md) instead.
