"""Protocol definition for the messaging service."""

from typing import Callable, Protocol, runtime_checkable

from messaging_app.models.message import Message
from messaging_app.models.user import User


@runtime_checkable
class MessagingServiceProtocol(Protocol):
    """Protocol defining the interface for messaging service implementations."""

    def get_current_user(self) -> User:
        """Return the currently authenticated user."""
        ...

    def get_contacts(self) -> list[User]:
        """Return the list of contacts for the current user."""
        ...

    def get_messages(self, contact_id: str) -> list[Message]:
        """Return all messages for the specified contact conversation."""
        ...

    def send_message(self, recipient_id: str, content: str) -> Message:
        """Send a message to a recipient and return the sent Message."""
        ...

    def add_contact(self, username: str, display_name: str) -> User:
        """Add a new contact and return the created User."""
        ...

    def subscribe_message_received(self, callback: Callable[[Message], None]) -> None:
        """Subscribe a callback to be notified when a new message is received."""
        ...

    def subscribe_contact_added(self, callback: Callable[[User], None]) -> None:
        """Subscribe a callback to be notified when a new contact is added."""
        ...
