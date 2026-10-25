"""User data model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    """Represents a chat user/contact in the messaging system."""

    id: str
    username: str
    display_name: str
    avatar_initials: str
    is_online: bool = False
