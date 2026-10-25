"""Integration tests for the main MessagingApp root window and workflow."""

from datetime import datetime
from pathlib import Path
import sys
import time
from unittest.mock import MagicMock

import customtkinter
import pytest

# Ensure src is in sys.path for standalone pytest invocations
_SRC_PATH = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_PATH not in sys.path:
    sys.path.insert(0, _SRC_PATH)

from messaging_app.models.message import Message
from messaging_app.models.user import User
from messaging_app.services.dummy_service import DummyMessagingService
from messaging_app.ui.app import MessagingApp
from messaging_app.ui.components.add_user_modal import AddUserModal
from messaging_app.ui.components.chat_area import ChatArea
from messaging_app.ui.components.sidebar import Sidebar
from messaging_app.ui.icons import _ICON_CACHE


@pytest.fixture(autouse=True)
def _clean_icons_and_tk():
    """Ensure clean icon cache and brief pause between Tkinter window initializations."""
    _ICON_CACHE.clear()
    yield
    _ICON_CACHE.clear()
    time.sleep(0.05)


def _create_app(service: DummyMessagingService, max_retries: int = 3) -> MessagingApp:
    """Create MessagingApp instance with automatic retry on transient Tkinter initialization locks."""
    for attempt in range(max_retries):
        try:
            return MessagingApp(service=service)
        except Exception:
            if attempt == max_retries - 1:
                raise
            time.sleep(0.1)
    return MessagingApp(service=service)


def test_app_integration_flow() -> None:
    """Verify primary end-to-end integration flow from task brief."""
    service = DummyMessagingService(simulation_delay=0.05)
    app = _create_app(service=service)
    try:
        # Initial state check
        displayed = app.sidebar.get_displayed_contacts()
        assert len(displayed) >= 3
        alice = displayed[0]

        # Select contact
        app.select_contact(alice)
        assert app.chat_area.active_contact is not None
        assert app.chat_area.active_contact.id == alice.id

        # Send message through app
        app.handle_send_message("Integration test hello!")
        history = service.get_messages(alice.id)
        assert any(m.content == "Integration test hello!" for m in history)

        # Add contact through app
        new_user = app.handle_add_contact("eva", "Eva Green")
        assert new_user.username == "eva"
        assert any(c.username == "eva" for c in app.sidebar.get_displayed_contacts())

        # Allow simulated reply timer to complete and process safely
        time.sleep(0.15)
        try:
            app.update()
        except Exception:
            pass
    finally:
        app.destroy()


def test_app_window_configuration_and_layout() -> None:
    """Verify root window properties, geometry, minsize, and grid structure."""
    service = DummyMessagingService(simulation_delay=0)
    app = _create_app(service=service)
    try:
        assert "NexusChat — Python Messaging App" in app.title()
        assert isinstance(app.sidebar, Sidebar)
        assert isinstance(app.chat_area, ChatArea)

        # Verify grid layout assignment
        sidebar_info = app.sidebar.grid_info()
        chat_info = app.chat_area.grid_info()
        assert sidebar_info["column"] == 0 or sidebar_info["column"] == "0"
        assert chat_info["column"] == 1 or chat_info["column"] == "1"
    finally:
        app.destroy()


def test_app_theme_toggle() -> None:
    """Verify theme toggling switches between Dark and Light appearance modes."""
    service = DummyMessagingService(simulation_delay=0)
    app = _create_app(service=service)
    try:
        customtkinter.set_appearance_mode("Dark")
        assert customtkinter.get_appearance_mode().lower() == "dark"

        app.toggle_theme()
        assert customtkinter.get_appearance_mode().lower() == "light"

        app.toggle_theme()
        assert customtkinter.get_appearance_mode().lower() == "dark"
    finally:
        app.destroy()


def test_app_incoming_message_subscription_thread_safe() -> None:
    """Verify incoming messages dispatch through thread-safe UI update handlers."""
    service = DummyMessagingService(simulation_delay=0)
    app = _create_app(service=service)
    try:
        contacts = service.get_contacts()
        alice = contacts[0]
        bob = contacts[1]
        app.select_contact(alice)

        # Message for active contact (Alice)
        msg_alice = Message(
            id="test-msg-1",
            sender_id=alice.id,
            recipient_id="me",
            content="Hello from Alice!",
            timestamp=datetime.now(),
            is_outgoing=False,
        )
        app._handle_incoming_message_ui(msg_alice)
        assert any(m.content == "Hello from Alice!" for m in app.chat_area._messages)

        # Message from non-active contact (Bob) should NOT appear in Alice's active stream
        msg_bob = Message(
            id="test-msg-2",
            sender_id=bob.id,
            recipient_id="me",
            content="Hello from Bob!",
            timestamp=datetime.now(),
            is_outgoing=False,
        )
        app._handle_incoming_message_ui(msg_bob)
        assert not any(m.content == "Hello from Bob!" for m in app.chat_area._messages)
    finally:
        app.destroy()


def test_app_contact_added_subscription_updates_ui() -> None:
    """Verify contact addition notification refreshes sidebar and selects the new user."""
    service = DummyMessagingService(simulation_delay=0)
    app = _create_app(service=service)
    try:
        new_contact = service.add_contact("frank", "Frank Ocean")
        app._handle_contact_added_ui(new_contact)

        assert any(c.username == "frank" for c in app.sidebar.get_displayed_contacts())
        assert app.chat_area.active_contact is not None
        assert app.chat_area.active_contact.username == "frank"
    finally:
        app.destroy()


def test_app_modal_dialog_lifecycle_and_validation() -> None:
    """Verify opening dialog, handling duplicate open, validation error, and successful add."""
    service = DummyMessagingService(simulation_delay=0)
    app = _create_app(service=service)
    try:
        # Open dialog
        app.open_add_contact_dialog()
        assert app._modal_instance is not None
        assert isinstance(app._modal_instance, AddUserModal)
        modal = app._modal_instance
        assert modal.winfo_exists()

        # Opening again should not duplicate, but focus existing
        app.open_add_contact_dialog()
        assert app._modal_instance is modal

        # Attempt to submit empty username -> should trigger validation error on modal
        app._handle_modal_submit("", "Some Name")
        assert modal.winfo_exists()
        assert "cannot be empty" in modal.error_label.cget("text")

        # Attempt to add existing username -> should trigger Duplicate username ValueError
        alice_username = service.get_contacts()[0].username
        app._handle_modal_submit(alice_username, "Duplicate Alice")
        assert modal.winfo_exists()
        assert "already exists" in modal.error_label.cget("text")

        # Successful submission
        app._handle_modal_submit("grace", "Grace Hopper")
        assert any(c.username == "grace" for c in app.sidebar.get_displayed_contacts())
        assert app._modal_instance is None
    finally:
        app.destroy()


def test_main_entry_point(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify application main() entry point initializes service and starts event loop."""
    import messaging_app.main as main_module

    mock_app_cls = MagicMock()
    mock_instance = MagicMock()
    mock_app_cls.return_value = mock_instance

    monkeypatch.setattr(main_module, "MessagingApp", mock_app_cls)

    main_module.main()

    assert mock_app_cls.called
    assert isinstance(mock_app_cls.call_args[1]["service"], DummyMessagingService)
    assert mock_instance.mainloop.called

