"""Application configuration loaded from environment variables / .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All settings can be overridden via environment variables or the .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Server -------------------------------------------------------------
    server_name: str = "IT Support Ticket MCP Server"
    host: str = "0.0.0.0"
    port: int = 8989
    mcp_path: str = "/mcp"

    # --- Database -----------------------------------------------------------
    database_url: str = "sqlite:///./data/tickets.db"
    seed_data: bool = True

    # --- Logging ------------------------------------------------------------
    log_level: str = "INFO"
    log_to_file: bool = True
    log_dir: str = "./logs"
    log_file: str = "ticket-mcp.log"
    log_max_bytes: int = 1_048_576  # 1 MB
    log_backup_count: int = 5

    @property
    def sqlite_path(self) -> Path | None:
        """Filesystem path of the SQLite DB (None for in-memory / non-sqlite URLs)."""
        prefix = "sqlite:///"
        if self.database_url.startswith(prefix):
            raw = self.database_url[len(prefix) :]
            if raw and raw != ":memory:":
                return Path(raw)
        return None

    @property
    def log_path(self) -> Path:
        return Path(self.log_dir) / self.log_file


@lru_cache
def get_settings() -> Settings:
    return Settings()
