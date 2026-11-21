"""Local SQLite database cache for persistent offline chat history and contacts."""

from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import sqlite3
import threading

from messaging_app.models.message import Message
from messaging_app.models.user import User


class DatabaseCache:
    """Thread-safe SQLite repository managing contacts and messages."""

    def __init__(self, db_path: Path | str) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_schema()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager yielding an active SQLite connection and guaranteeing closure."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._lock, self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS contacts (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    avatar_initials TEXT NOT NULL,
                    is_online INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    sender_id TEXT NOT NULL,
                    recipient_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    is_outgoing INTEGER NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_messages_pair 
                ON messages(sender_id, recipient_id, timestamp);

                CREATE INDEX IF NOT EXISTS idx_messages_recipient_ts 
                ON messages(recipient_id, timestamp);
                """
            )

    def save_message(self, message: Message) -> None:
        """Persist or update a message in the local SQLite store."""
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO messages 
                (id, sender_id, recipient_id, content, timestamp, is_outgoing)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    message.id,
                    message.sender_id,
                    message.recipient_id,
                    message.content,
                    message.timestamp.isoformat(),
                    1 if message.is_outgoing else 0,
                ),
            )

    def get_messages(self, contact_id: str) -> list[Message]:
        """Retrieve all messages exchanged with a specific contact in chronological order."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, sender_id, recipient_id, content, timestamp, is_outgoing
                FROM messages
                WHERE sender_id = ? OR recipient_id = ?
                ORDER BY timestamp ASC
                """,
                (contact_id, contact_id),
            )
            rows = cursor.fetchall()
            messages: list[Message] = []
            for row in rows:
                try:
                    ts = datetime.fromisoformat(row["timestamp"])
                except (ValueError, TypeError):
                    ts = datetime.now()
                messages.append(
                    Message(
                        id=row["id"],
                        sender_id=row["sender_id"],
                        recipient_id=row["recipient_id"],
                        content=row["content"],
                        timestamp=ts,
                        is_outgoing=bool(row["is_outgoing"]),
                    )
                )
            return messages

    def merge_history(self, server_messages: list[Message]) -> tuple[int, int]:
        """Merge server message history using INSERT OR IGNORE deduplication.
        
        Returns a tuple of (new_messages_count, duplicate_messages_count).
        """
        new_count = 0
        dup_count = 0
        with self._lock, self._get_connection() as conn:
            for msg in server_messages:
                cursor = conn.execute(
                    """
                    INSERT OR IGNORE INTO messages 
                    (id, sender_id, recipient_id, content, timestamp, is_outgoing)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        msg.id,
                        msg.sender_id,
                        msg.recipient_id,
                        msg.content,
                        msg.timestamp.isoformat(),
                        1 if msg.is_outgoing else 0,
                    ),
                )
                if cursor.rowcount > 0:
                    new_count += 1
                else:
                    dup_count += 1
        return new_count, dup_count

    def upsert_contact(self, user: User) -> None:
        """Insert or update contact details in the local SQLite store."""
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO contacts (id, username, display_name, avatar_initials, is_online)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    username=excluded.username,
                    display_name=excluded.display_name,
                    avatar_initials=excluded.avatar_initials,
                    is_online=excluded.is_online,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    user.id,
                    user.username,
                    user.display_name,
                    user.avatar_initials,
                    1 if user.is_online else 0,
                ),
            )

    def get_contacts(self) -> list[User]:
        """Retrieve all cached contacts sorted by online status (online first) then display_name."""
        with self._lock, self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, username, display_name, avatar_initials, is_online
                FROM contacts
                ORDER BY is_online DESC, display_name ASC
                """
            )
            rows = cursor.fetchall()
            return [
                User(
                    id=row["id"],
                    username=row["username"],
                    display_name=row["display_name"],
                    avatar_initials=row["avatar_initials"],
                    is_online=bool(row["is_online"]),
                )
                for row in rows
            ]

    def update_contact_status(self, user_id: str, is_online: bool) -> None:
        """Update the online presence status of a contact."""
        with self._lock, self._get_connection() as conn:
            conn.execute(
                "UPDATE contacts SET is_online = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (1 if is_online else 0, user_id),
            )
