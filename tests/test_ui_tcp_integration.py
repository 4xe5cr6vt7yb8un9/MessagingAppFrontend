"""Integration tests for TCP UI features: connection pill, presence updates, and modal verifying state."""

from pathlib import Path
import sys
import time
from unittest.mock import MagicMock

import customtkinter
import pytest

# Ensure src is in sys.path
_SRC_PATH = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_PATH not in sys.path:
    sys.path.insert(0, _SRC_PATH)

from messaging_app.models.user import User
from messaging_app.services.dummy_service import DummyMessagingService
from messaging_app.ui.app import MessagingApp
from messaging_app.ui.components.add_user_modal import AddUserModal
from messaging_app.ui.icons import _ICON_CACHE
from messaging_app.ui.theme import Theme


@pytest.fixture(autouse=True)
def _clean_icons_and_tk():
    """Ensure clean icon cache before and after each test."""
    _ICON_CACHE.clear()
    yield
    _ICON_CACHE.clear()
    time.sleep(0.05)


def test_sidebar_connection_status_update():
    """Verify that sidebar contains connection_pill and responds to connection status updates."""
    root = customtkinter.CTk()
    service = DummyMessagingService()
    app = MessagingApp(service=service)

    try:
        # Check that status pill exists on sidebar
        assert hasattr(app.sidebar, "connection_pill")

        # Test setting connection status
        app.sidebar.set_connection_status("CONNECTED", "127.0.0.1:9000")
        assert "Connected" in app.sidebar.connection_pill.cget("text")

        app.sidebar.set_connection_status("RECONNECTING", "refused")
        assert "Reconnecting" in app.sidebar.connection_pill.cget("text")

        app.sidebar.set_connection_status("DISCONNECTED", "")
        assert "Disconnected" in app.sidebar.connection_pill.cget("text")
    finally:
        app.destroy()
        try:
            root.destroy()
        except Exception:
            pass


def test_add_user_modal_verifying_state_and_error_reenable():
    """Verify modal disables submit button with 'Verifying...' and re-enables on error."""
    root = customtkinter.CTk()
    try:
        submitted_args: list[tuple[str, str]] = []

        def dummy_submit(username: str, display_name: str) -> None:
            submitted_args.append((username, display_name))

        modal = AddUserModal(root, on_submit=dummy_submit)
        modal.username_entry.insert(0, "alice")

        # Before submission
        assert modal.submit_btn.cget("text") == "Add Contact"
        assert modal.submit_btn.cget("state") == "normal"

        # Submit
        modal._handle_submit()
        assert len(submitted_args) == 1
        assert submitted_args[0] == ("alice", "")
        assert modal.submit_btn.cget("text") == "Verifying..."
        assert modal.submit_btn.cget("state") == "disabled"

        # On error feedback
        modal.set_error("User does not exist on server.")
        assert modal.error_label.cget("text") == "User does not exist on server."
        assert modal.submit_btn.cget("text") == "Add Contact"
        assert modal.submit_btn.cget("state") == "normal"

        modal.destroy()
    finally:
        root.destroy()


def test_app_presence_update_ui():
    """Verify _handle_presence_update_ui updates contact status dot in sidebar and chat header."""
    service = DummyMessagingService(simulation_delay=0)
    app = MessagingApp(service=service)
    try:
        contacts = service.get_contacts()
        alice = contacts[0]
        app.select_contact(alice)

        # Initially Alice is online
        assert "Online" in app.chat_area.header_status.cget("text")

        # Simulate presence update: Alice goes offline
        app._handle_presence_update_ui(alice.id, False)

        # Check chat header
        assert "Offline" in app.chat_area.header_status.cget("text")

        # Check sidebar contact card status dot
        if hasattr(app.sidebar, "_status_dot_widgets"):
            dot = app.sidebar._status_dot_widgets.get(alice.id)
            if dot:
                assert dot.cget("text_color") == Theme.STATUS_OFFLINE

        # Simulate presence update: Alice comes back online
        app._handle_presence_update_ui(alice.id, True)
        assert "Online" in app.chat_area.header_status.cget("text")
        if hasattr(app.sidebar, "_status_dot_widgets"):
            dot = app.sidebar._status_dot_widgets.get(alice.id)
            if dot:
                assert dot.cget("text_color") == Theme.STATUS_ONLINE
    finally:
        app.destroy()


def test_app_subscribes_to_connection_and_presence():
    """Verify MessagingApp subscribes to connection status and presence if supported by service."""
    status_cbs = []
    presence_cbs = []

    class MockTcpService(DummyMessagingService):
        def subscribe_connection_status(self, callback):
            status_cbs.append(callback)

        def subscribe_presence_updated(self, callback):
            presence_cbs.append(callback)

    mock_service = MockTcpService()
    app = MessagingApp(service=mock_service)
    try:
        assert len(status_cbs) == 1
        assert len(presence_cbs) == 1
    finally:
        app.destroy()
