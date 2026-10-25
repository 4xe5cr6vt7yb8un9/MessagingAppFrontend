"""Unit tests for User and Message data models."""

from datetime import datetime
from pathlib import Path
import sys

import pytest

# Ensure src is in sys.path for standalone pytest invocations
_SRC_PATH = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_PATH not in sys.path:
    sys.path.insert(0, _SRC_PATH)

from messaging_app.models import Message, User
from messaging_app.models.message import Message as DirectMessage
from messaging_app.models.user import User as DirectUser


def test_models_package_exports() -> None:
    """Verify that models __init__ exposes User and Message."""
    assert User is DirectUser
    assert Message is DirectMessage


def test_user_creation_and_immutability() -> None:
    """Verify User attributes and immutability."""
    user = User(
        id="u1",
        username="alice",
        display_name="Alice Smith",
        avatar_initials="AS",
        is_online=True,
    )
    assert user.id == "u1"
    assert user.username == "alice"
    assert user.display_name == "Alice Smith"
    assert user.avatar_initials == "AS"
    assert user.is_online is True

    with pytest.raises(Exception):
        user.display_name = "Alice Doe"  # type: ignore[misc]


def test_user_defaults() -> None:
    """Verify default values for User."""
    user = User(
        id="u2",
        username="bob",
        display_name="Bob Jones",
        avatar_initials="BJ",
    )
    assert user.is_online is False


def test_message_creation_and_defaults() -> None:
    """Verify Message attributes, default timestamp, and immutability."""
    msg = Message(
        id="m1",
        sender_id="u1",
        recipient_id="u2",
        content="Hello world!",
        is_outgoing=True,
    )
    assert msg.id == "m1"
    assert msg.sender_id == "u1"
    assert msg.recipient_id == "u2"
    assert msg.content == "Hello world!"
    assert msg.is_outgoing is True
    assert isinstance(msg.timestamp, datetime)

    with pytest.raises(Exception):
        msg.content = "Mutated"  # type: ignore[misc]


def test_message_defaults() -> None:
    """Verify default values for Message."""
    msg = Message(
        id="m2",
        sender_id="u1",
        recipient_id="u2",
        content="Default check",
    )
    assert msg.is_outgoing is False
    assert isinstance(msg.timestamp, datetime)
