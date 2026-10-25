"""Tests for MessagingServiceProtocol and DummyMessagingService."""

import time
from pathlib import Path
import sys
import pytest

# Ensure src is in sys.path for standalone pytest invocations
_SRC_PATH = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_PATH not in sys.path:
    sys.path.insert(0, _SRC_PATH)

from messaging_app.models.message import Message
from messaging_app.models.user import User
from messaging_app.services.dummy_service import DummyMessagingService
from messaging_app.services.protocol import MessagingServiceProtocol


def test_dummy_service_implements_protocol() -> None:
    service = DummyMessagingService()
    assert isinstance(service, MessagingServiceProtocol)


def test_initial_contacts_and_current_user() -> None:
    service = DummyMessagingService()
    current_user = service.get_current_user()
    assert current_user.username == "me"

    contacts = service.get_contacts()
    assert len(contacts) >= 3
    alice = next((c for c in contacts if c.username == "alice"), None)
    assert alice is not None
    assert alice.display_name == "Alice Smith"


def test_send_message_and_simulation() -> None:
    service = DummyMessagingService(simulation_delay=0.05)
    received_replies: list[Message] = []
    service.subscribe_message_received(lambda msg: received_replies.append(msg))

    msg = service.send_message(recipient_id="alice", content="Hey Alice!")
    assert msg.content == "Hey Alice!"
    assert msg.is_outgoing is True

    # Check that outgoing message is stored in conversation
    history = service.get_messages("alice")
    assert any(m.id == msg.id for m in history)

    # Wait for simulated reply
    time.sleep(0.15)
    assert len(received_replies) == 1
    assert received_replies[0].sender_id == "alice"
    assert received_replies[0].is_outgoing is False


def test_send_message_empty_content_raises() -> None:
    service = DummyMessagingService(simulation_delay=0)
    with pytest.raises(ValueError, match="cannot be empty"):
        service.send_message(recipient_id="alice", content="   ")


def test_get_messages_unknown_contact_returns_empty_list() -> None:
    service = DummyMessagingService()
    assert service.get_messages("nonexistent_user") == []


def test_defensive_copy_contacts_and_messages() -> None:
    service = DummyMessagingService()
    contacts = service.get_contacts()
    contacts.clear()
    assert len(service.get_contacts()) > 0

    history = service.get_messages("alice")
    history.clear()
    assert len(service.get_messages("alice")) > 0


def test_add_contact_success_and_validation() -> None:
    service = DummyMessagingService()
    added_users: list[User] = []
    service.subscribe_contact_added(lambda u: added_users.append(u))

    new_user = service.add_contact(username="david", display_name="David Miller")
    assert new_user.username == "david"
    assert new_user.avatar_initials == "DM"
    assert len(added_users) == 1

    # Check duplicate prevention
    with pytest.raises(ValueError, match="already exists"):
        service.add_contact(username="david", display_name="David Clone")

    # Check empty username prevention
    with pytest.raises(ValueError, match="cannot be empty"):
        service.add_contact(username="   ", display_name="Invalid")

    # Check strip leading @ and fallback display name
    eve = service.add_contact(username=" @eve ", display_name="")
    assert eve.username == "eve"
    assert eve.display_name == "Eve"
