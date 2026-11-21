"""Application configuration loader from .env file."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    """Strongly typed application configuration settings."""

    server_ip: str
    server_port: int
    client_user_id: str
    client_username: str
    client_display_name: str
    local_db_path: Path

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> AppConfig:
        """Load configuration from .env or environment variables with sane defaults."""
        if env_path is not None:
            if env_path.exists():
                load_dotenv(env_path, override=True)
        else:
            load_dotenv(override=False)

        server_port_str = os.getenv("SERVER_PORT", "9000")
        try:
            server_port = int(server_port_str)
        except ValueError:
            server_port = 9000

        return cls(
            server_ip=os.getenv("SERVER_IP", "127.0.0.1"),
            server_port=server_port,
            client_user_id=os.getenv("CLIENT_USER_ID", "user_me"),
            client_username=os.getenv("CLIENT_USERNAME", "me"),
            client_display_name=os.getenv("CLIENT_DISPLAY_NAME", "You"),
            local_db_path=Path(os.getenv("LOCAL_DB_PATH", "data/chat_cache.db")),
        )
