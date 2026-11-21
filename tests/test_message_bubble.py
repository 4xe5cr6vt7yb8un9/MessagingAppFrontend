"""Unit tests for MessageBubble component."""

from datetime import datetime
from pathlib import Path
import sys

import customtkinter
import pytest

# Ensure src is in sys.path for standalone pytest invocations
_SRC_PATH = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_PATH not in sys.path:
    sys.path.insert(0, _SRC_PATH)

from messaging_app.models.message import Message
from messaging_app.ui.components import MessageBubble
from messaging_app.ui.components.message_bubble import MessageBubble as DirectMessageBubble


@pytest.fixture(scope="module")
def root():
    """Shared CTk root window for message bubble tests to avoid repeated Tk interpreter cycles."""
    r = customtkinter.CTk()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


def test_components_package_exports() -> None:
    """Verify that components __init__ exposes MessageBubble."""
    assert MessageBubble is DirectMessageBubble


def test_message_bubble_creation_outgoing(root) -> None:
    """Verify outgoing message bubble creation and layout configuration."""
    msg = Message(
        id="m1",
        sender_id="user1",
        recipient_id="user2",
        content="Hello from me!",
        timestamp=datetime(2026, 10, 25, 14, 30),
        is_outgoing=True,
    )
    bubble = MessageBubble(root, message=msg, contact_initials="AS")
    try:
        assert bubble.message.content == "Hello from me!"
        assert bubble.message.is_outgoing is True
        assert bubble.avatar is None
        assert bubble.text_label.cget("text") == "Hello from me!"
        assert "02:30 PM" in bubble.time_label.cget("text")
    finally:
        if bubble.winfo_exists():
            bubble.destroy()


def test_message_bubble_creation_incoming(root) -> None:
    """Verify incoming message bubble creation and avatar initial."""
    msg = Message(
        id="m2",
        sender_id="user2",
        recipient_id="user1",
        content="Hello back!",
        timestamp=datetime(2026, 10, 25, 9, 15),
        is_outgoing=False,
    )
    bubble = MessageBubble(root, message=msg, contact_initials="JD")
    try:
        assert bubble.message.content == "Hello back!"
        assert bubble.message.is_outgoing is False
        assert bubble.avatar is not None
        assert bubble.avatar.cget("text") == "JD"
        assert bubble.text_label.cget("text") == "Hello back!"
        assert "09:15 AM" in bubble.time_label.cget("text")
    finally:
        if bubble.winfo_exists():
            bubble.destroy()


def test_message_bubble_incoming_default_initials(root) -> None:
    """Verify incoming message bubble fallback initials when empty string is provided."""
    msg = Message(
        id="m3",
        sender_id="user2",
        recipient_id="user1",
        content="No initials message",
        is_outgoing=False,
    )
    bubble = MessageBubble(root, message=msg)
    try:
        assert bubble.avatar is not None
        assert bubble.avatar.cget("text") == "??"
    finally:
        if bubble.winfo_exists():
            bubble.destroy()
