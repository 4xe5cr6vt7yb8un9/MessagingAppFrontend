"""Unit tests for application entry point and CLI flag parsing."""

from pathlib import Path
import sys
from unittest.mock import MagicMock, patch
import pytest

# Ensure src directory is in sys.path
_SRC_PATH = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_PATH not in sys.path:
    sys.path.insert(0, _SRC_PATH)

from messaging_app.config import AppConfig
import messaging_app.main as main_module


def test_main_help_flag_long(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify --help flag prints usage, supported env vars, and exits without service startup."""
    monkeypatch.setattr(sys, "argv", ["messaging_app", "--help"])
    mock_service_cls = MagicMock()
    mock_app_cls = MagicMock()
    monkeypatch.setattr(main_module, "TcpMessagingService", mock_service_cls)
    monkeypatch.setattr(main_module, "MessagingApp", mock_app_cls)

    main_module.main()

    captured = capsys.readouterr().out
    assert "NexusChat - Modern Desktop Messaging Application" in captured
    assert "--help" in captured
    assert "SERVER_IP" in captured
    assert "CLIENT_USER_ID" in captured
    assert mock_service_cls.call_count == 0
    assert mock_app_cls.call_count == 0


def test_main_help_flag_short(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify -h flag prints usage and exits without initializing services."""
    monkeypatch.setattr(sys, "argv", ["messaging_app", "-h"])
    mock_service_cls = MagicMock()
    mock_app_cls = MagicMock()
    monkeypatch.setattr(main_module, "TcpMessagingService", mock_service_cls)
    monkeypatch.setattr(main_module, "MessagingApp", mock_app_cls)

    main_module.main()

    captured = capsys.readouterr().out
    assert "NexusChat - Modern Desktop Messaging Application" in captured
    assert "-h, --help" in captured
    assert mock_service_cls.call_count == 0
    assert mock_app_cls.call_count == 0


def test_main_orchestration_and_clean_teardown(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify end-to-end component creation, start, mainloop, and graceful teardown in finally."""
    monkeypatch.setattr(sys, "argv", ["messaging_app"])

    mock_config = AppConfig(
        server_ip="192.168.1.100",
        server_port=9999,
        client_user_id="user-123",
        client_username="alex",
        client_display_name="Alex Mercer",
        local_db_path=Path("data/test.db"),
    )

    mock_from_env = MagicMock(return_value=mock_config)
    mock_db_cache = MagicMock()
    mock_db_cls = MagicMock(return_value=mock_db_cache)
    mock_service = MagicMock()
    mock_service_cls = MagicMock(return_value=mock_service)
    mock_app = MagicMock()
    mock_app_cls = MagicMock(return_value=mock_app)

    monkeypatch.setattr(main_module.AppConfig, "from_env", mock_from_env)
    monkeypatch.setattr(main_module, "DatabaseCache", mock_db_cls)
    monkeypatch.setattr(main_module, "TcpMessagingService", mock_service_cls)
    monkeypatch.setattr(main_module, "MessagingApp", mock_app_cls)

    main_module.main()

    # 1. Config loaded
    mock_from_env.assert_called_once()

    # 2. DatabaseCache initialized with local_db_path
    mock_db_cls.assert_called_once_with(mock_config.local_db_path)

    # 3. TcpMessagingService initialized with config and cache
    mock_service_cls.assert_called_once_with(config=mock_config, db_cache=mock_db_cache)

    # 4. Service started
    mock_service.start.assert_called_once()

    # 5. UI initialized and run
    mock_app_cls.assert_called_once_with(service=mock_service)
    mock_app.mainloop.assert_called_once()

    # 6. Service stopped on clean exit
    mock_service.stop.assert_called_once()


def test_main_teardown_on_mainloop_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify service.stop() is executed in finally: block if mainloop raises an exception."""
    monkeypatch.setattr(sys, "argv", ["messaging_app"])

    mock_service = MagicMock()
    mock_service_cls = MagicMock(return_value=mock_service)
    mock_app = MagicMock()
    mock_app.mainloop.side_effect = RuntimeError("Unexpected UI loop crash")
    mock_app_cls = MagicMock(return_value=mock_app)

    monkeypatch.setattr(main_module, "DatabaseCache", MagicMock())
    monkeypatch.setattr(main_module, "TcpMessagingService", mock_service_cls)
    monkeypatch.setattr(main_module, "MessagingApp", mock_app_cls)

    with pytest.raises(RuntimeError, match="Unexpected UI loop crash"):
        main_module.main()

    mock_service.start.assert_called_once()
    mock_service.stop.assert_called_once()


def test_main_teardown_on_app_init_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify service.stop() is executed in finally: block if MessagingApp init raises."""
    monkeypatch.setattr(sys, "argv", ["messaging_app"])

    mock_service = MagicMock()
    mock_service_cls = MagicMock(return_value=mock_service)
    mock_app_cls = MagicMock(side_effect=RuntimeError("Display connection failed"))

    monkeypatch.setattr(main_module, "DatabaseCache", MagicMock())
    monkeypatch.setattr(main_module, "TcpMessagingService", mock_service_cls)
    monkeypatch.setattr(main_module, "MessagingApp", mock_app_cls)

    with pytest.raises(RuntimeError, match="Display connection failed"):
        main_module.main()

    mock_service.start.assert_called_once()
    mock_service.stop.assert_called_once()
