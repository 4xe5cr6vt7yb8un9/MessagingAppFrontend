"""In-memory interactive dummy messaging service implementation."""

from datetime import datetime
import random
import threading
from typing import Callable
import uuid

from messaging_app.models.message import Message
from messaging_app.models.user import User


class DummyMessagingService:
    """In-memory interactive dummy messaging service with realistic simulation."""

    def __init__(self, simulation_delay: float = 1.2) -> None:
        self.simulation_delay = simulation_delay
        self._lock = threading.Lock()
        self._message_callbacks: list[Callable[[Message], None]] = []
        self._contact_callbacks: list[Callable[[User], None]] = []

        self._current_user = User(
            id="me",
            username="me",
            display_name="You",
            avatar_initials="ME",
            is_online=True,
        )

        self._contacts: list[User] = [
            User(id="alice", username="alice", display_name="Alice Smith", avatar_initials="AS", is_online=True),
            User(id="bob", username="bob", display_name="Bob Martinez", avatar_initials="BM", is_online=False),
            User(id="charlie", username="charlie", display_name="Charlie Kim", avatar_initials="CK", is_online=True),
        ]

        self._messages: dict[str, list[Message]] = {
            "alice": [
                Message(
                    id="m1",
                    sender_id="alice",
                    recipient_id="me",
                    content="Hi there! How is the project going?",
                    timestamp=datetime.now(),
                    is_outgoing=False,
                ),
                Message(
                    id="m2",
                    sender_id="me",
                    recipient_id="alice",
                    content="Making great progress on the frontend!",
                    timestamp=datetime.now(),
                    is_outgoing=True,
                ),
            ],
            "bob": [
                Message(
                    id="m3",
                    sender_id="bob",
                    recipient_id="me",
                    content="Catch you tomorrow!",
                    timestamp=datetime.now(),
                    is_outgoing=False,
                ),
            ],
            "charlie": [
                Message(
                    id="m4",
                    sender_id="charlie",
                    recipient_id="me",
                    content="Hey, do you have that report?",
                    timestamp=datetime.now(),
                    is_outgoing=False,
                ),
            ],
        }

        self._simulation_responses: list[str] = [
            "Got it! That sounds great.",
            "Thanks for reaching out! Let me check on that.",
            "Sounds good to me 👍",
            "Awesome, I'll review and reply shortly.",
            "Understood! Let's follow up on that.",
        ]

    def get_current_user(self) -> User:
        """Return the current logged-in user."""
        return self._current_user

    def get_contacts(self) -> list[User]:
        """Return a copy of the contacts list."""
        with self._lock:
            return list(self._contacts)

    def get_messages(self, contact_id: str) -> list[Message]:
        """Return a copy of the message list for the specified contact."""
        with self._lock:
            return list(self._messages.get(contact_id, []))

    def send_message(self, recipient_id: str, content: str) -> Message:
        """Send a message to a recipient and trigger simulated reply if configured."""
        cleaned_content = content.strip()
        if not cleaned_content:
            raise ValueError("Message content cannot be empty.")

        msg = Message(
            id=str(uuid.uuid4())[:8],
            sender_id=self._current_user.id,
            recipient_id=recipient_id,
            content=cleaned_content,
            timestamp=datetime.now(),
            is_outgoing=True,
        )

        with self._lock:
            if recipient_id not in self._messages:
                self._messages[recipient_id] = []
            self._messages[recipient_id].append(msg)

        if self.simulation_delay > 0:
            timer = threading.Timer(
                self.simulation_delay,
                self._dispatch_simulated_reply,
                args=(recipient_id,),
            )
            timer.daemon = True
            timer.start()

        return msg

    def _dispatch_simulated_reply(self, contact_id: str) -> None:
        """Dispatch a simulated automatic reply from a contact."""
        reply_text = random.choice(self._simulation_responses)
        reply_msg = Message(
            id=str(uuid.uuid4())[:8],
            sender_id=contact_id,
            recipient_id=self._current_user.id,
            content=reply_text,
            timestamp=datetime.now(),
            is_outgoing=False,
        )

        with self._lock:
            if contact_id not in self._messages:
                self._messages[contact_id] = []
            self._messages[contact_id].append(reply_msg)
            callbacks = list(self._message_callbacks)

        for callback in callbacks:
            callback(reply_msg)

    def add_contact(self, username: str, display_name: str) -> User:
        """Validate and add a new contact."""
        clean_user = username.strip().lstrip("@")
        clean_name = display_name.strip()

        if not clean_user:
            raise ValueError("Username cannot be empty.")
        if not clean_name:
            clean_name = clean_user.capitalize()

        with self._lock:
            if any(c.username.lower() == clean_user.lower() for c in self._contacts):
                raise ValueError(f"Contact @{clean_user} already exists.")

            parts = clean_name.split()
            initials = (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()
            if not initials:
                initials = clean_user[:2].upper()

            new_user = User(
                id=clean_user.lower(),
                username=clean_user.lower(),
                display_name=clean_name,
                avatar_initials=initials,
                is_online=True,
            )
            self._contacts.append(new_user)
            self._messages[new_user.id] = []
            callbacks = list(self._contact_callbacks)

        for callback in callbacks:
            callback(new_user)

        return new_user

    def subscribe_message_received(self, callback: Callable[[Message], None]) -> None:
        """Register a callback for incoming messages."""
        with self._lock:
            self._message_callbacks.append(callback)

    def subscribe_contact_added(self, callback: Callable[[User], None]) -> None:
        """Register a callback for newly added contacts."""
        with self._lock:
            self._contact_callbacks.append(callback)
