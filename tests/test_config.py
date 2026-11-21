"""Unit tests for AppConfig and environment configuration loader."""

from pathlib import Path
import os
import pytest
from messaging_app.config import AppConfig


def test_config_defaults(tmp_path: Path):
    empty_env = tmp_path / ".empty_env"
    empty_env.write_text("", encoding="utf-8")

    # Temporarily clear env vars
    old_env = {
        k: os.environ.pop(k, None)
        for k in [
            "SERVER_IP",
            "SERVER_PORT",
            "CLIENT_USER_ID",
            "CLIENT_USERNAME",
            "CLIENT_DISPLAY_NAME",
            "LOCAL_DB_PATH",
        ]
    }
    try:
        config = AppConfig.from_env(env_path=empty_env)
        assert config.server_ip == "127.0.0.1"
        assert config.server_port == 9000
        assert config.client_user_id == "user_me"
        assert config.client_username == "me"
        assert config.client_display_name == "You"
        assert config.local_db_path == Path("data/chat_cache.db")
    finally:
        for k, v in old_env.items():
            if v is not None:
                os.environ[k] = v


def test_config_custom_values(tmp_path: Path):
    custom_env = tmp_path / ".custom_env"
    custom_env.write_text(
        "SERVER_IP=192.168.1.50\n"
        "SERVER_PORT=8080\n"
        "CLIENT_USER_ID=user_charlie\n"
        "CLIENT_USERNAME=charlie\n"
        "CLIENT_DISPLAY_NAME=Charlie Brown\n"
        "LOCAL_DB_PATH=data/custom.db\n",
        encoding="utf-8",
    )
    config = AppConfig.from_env(env_path=custom_env)
    assert config.server_ip == "192.168.1.50"
    assert config.server_port == 8080
    assert config.client_user_id == "user_charlie"
    assert config.client_username == "charlie"
    assert config.client_display_name == "Charlie Brown"
    assert config.local_db_path == Path("data/custom.db")


def test_config_invalid_port_fallback(tmp_path: Path):
    invalid_env = tmp_path / ".invalid_port_env"
    invalid_env.write_text("SERVER_PORT=not_a_number\n", encoding="utf-8")
    config = AppConfig.from_env(env_path=invalid_env)
    assert config.server_port == 9000


def test_config_immutable():
    config = AppConfig(
        server_ip="127.0.0.1",
        server_port=9000,
        client_user_id="user_me",
        client_username="me",
        client_display_name="You",
        local_db_path=Path("data/chat_cache.db"),
    )
    with pytest.raises(Exception):
        config.server_ip = "10.0.0.1"  # type: ignore[misc]
