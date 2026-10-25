"""Unit tests for ChatArea component."""

from pathlib import Path
import sys
from unittest.mock import MagicMock

import customtkinter
import pytest

# Ensure src is in sys.path for standalone pytest invocations
_SRC_PATH = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_PATH not in sys.path:
    sys.path.insert(0, _SRC_PATH)

from messaging_app.models.message import Message
from messaging_app.models.user import User
from messaging_app.ui.components import ChatArea
from messaging_app.ui.components.chat_area import ChatArea as DirectChatArea
from messaging_app.ui.icons import _ICON_CACHE
from messaging_app.ui.theme import Theme


@pytest.fixture(autouse=True)
def _clean_icons_and_tk():
    """Ensure clean icon cache before and after each test."""
    _ICON_CACHE.clear()
    yield
    _ICON_CACHE.clear()


def test_components_package_exports() -> None:
    """Verify that components __init__ exposes ChatArea."""
    assert ChatArea is DirectChatArea


def test_chat_area_creation_and_messaging() -> None:
    """Verify initialization, contact binding, and message appending."""
    root = customtkinter.CTk()
    try:
        sent_payloads: list[str] = []
        chat_area = ChatArea(root, on_send_message=lambda text: sent_payloads.append(text))
        chat_area.pack(fill="both", expand=True)

        assert chat_area.active_contact is None
        assert chat_area.header_name.cget("text") == ""
        assert chat_area.header_status.cget("text") == ""
        assert chat_area.header_avatar.cget("text") == ""

        alice = User("alice", "alice", "Alice Smith", "AS", True)
        chat_area.set_active_contact(alice)
        assert chat_area.active_contact == alice
        assert chat_area.header_name.cget("text") == "Alice Smith"
        assert chat_area.header_avatar.cget("text") == "AS"
        assert "Online" in chat_area.header_status.cget("text")

        msg = Message("m1", "alice", "me", "Hello from Alice", is_outgoing=False)
        chat_area.append_message(msg)
        assert len(chat_area.get_messages()) == 1
        assert chat_area.get_messages()[0].content == "Hello from Alice"
    finally:
        root.destroy()


def test_chat_area_offline_contact() -> None:
    """Verify offline contact header status styling."""
    root = customtkinter.CTk()
    try:
        chat_area = ChatArea(root, on_send_message=lambda t: None)
        bob = User("bob", "bob", "Bob Martinez", "BM", False)

        chat_area.set_active_contact(bob)
        assert chat_area.active_contact == bob
        assert chat_area.header_name.cget("text") == "Bob Martinez"
        assert chat_area.header_avatar.cget("text") == "BM"
        assert "Offline" in chat_area.header_status.cget("text")
    finally:
        root.destroy()


def test_chat_area_set_messages() -> None:
    """Verify setting batch of messages populates the stream and replaces existing."""
    root = customtkinter.CTk()
    try:
        chat_area = ChatArea(root, on_send_message=lambda t: None)
        alice = User("alice", "alice", "Alice Smith", "AS", True)
        chat_area.set_active_contact(alice)

        messages = [
            Message("m1", "alice", "me", "Hello", is_outgoing=False),
            Message("m2", "me", "alice", "Hi Alice", is_outgoing=True),
        ]
        chat_area.set_messages(messages)
        assert len(chat_area.get_messages()) == 2

        # Replace with single message
        new_messages = [Message("m3", "alice", "me", "New topic", is_outgoing=False)]
        chat_area.set_messages(new_messages)
        assert len(chat_area.get_messages()) == 1
        assert chat_area.get_messages()[0].id == "m3"
    finally:
        root.destroy()


def test_chat_area_send_interactions() -> None:
    """Verify composer entry send on button click and Return key."""
    root = customtkinter.CTk()
    try:
        on_send_mock = MagicMock()
        chat_area = ChatArea(root, on_send_message=on_send_mock)

        # 1. Send via button invoke with valid text
        chat_area.input_entry.delete(0, "end")
        chat_area.input_entry.insert(0, "Hello World")
        chat_area.send_btn.invoke()

        assert on_send_mock.call_count == 1
        assert on_send_mock.call_args[0][0] == "Hello World"
        assert chat_area.input_entry.get() == ""

        # 2. Whitespace only should not send
        chat_area.input_entry.insert(0, "   ")
        chat_area.send_btn.invoke()
        assert on_send_mock.call_count == 1

        # 3. Send via Return key handling
        chat_area.input_entry.delete(0, "end")
        chat_area.input_entry.insert(0, "Pressing enter")
        chat_area._handle_enter(None)
        assert on_send_mock.call_count == 2
        assert on_send_mock.call_args[0][0] == "Pressing enter"
        assert chat_area.input_entry.get() == ""
    finally:
        root.destroy()


def test_chat_area_reset_to_none_contact() -> None:
    """Verify setting contact to None restores empty state and clears header."""
    root = customtkinter.CTk()
    try:
        chat_area = ChatArea(root, on_send_message=lambda t: None)
        alice = User("alice", "alice", "Alice Smith", "AS", True)
        chat_area.set_active_contact(alice)
        chat_area.append_message(Message("m1", "alice", "me", "Hi", is_outgoing=False))

        assert chat_area.active_contact is not None
        assert len(chat_area.get_messages()) == 1

        # Reset to None
        chat_area.set_active_contact(None)
        assert chat_area.active_contact is None
        assert chat_area.header_name.cget("text") == ""
        assert chat_area.header_status.cget("text") == ""
        assert chat_area.header_avatar.cget("text") == ""
    finally:
        root.destroy()
