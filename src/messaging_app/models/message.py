"""Message data model."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Message:
    """Represents a single chat message."""

    id: str
    sender_id: str
    recipient_id: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    is_outgoing: bool = False
