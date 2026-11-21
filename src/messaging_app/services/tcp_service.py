"""Real TCP Messaging Service implementing MessagingServiceProtocol with SQLite cache."""

from datetime import datetime
import threading
from typing import Any, Callable
import uuid

from messaging_app.cache.database import DatabaseCache
from messaging_app.config import AppConfig
from messaging_app.models.message import Message
from messaging_app.models.user import User
from messaging_app.network.protocol_frames import (
    build_identify,
    build_query_user,
    build_send_message,
)
from messaging_app.network.tcp_client import TcpClient


class TcpMessagingService:
    """Coordinates local SQLite cache and background TcpClient socket."""

    def __init__(self, config: AppConfig, db_cache: DatabaseCache) -> None:
        self.config = config
        self.db = db_cache

        self._current_user = User(
            id=config.client_user_id,
            username=config.client_username,
            display_name=config.client_display_name,
            avatar_initials=self._compute_initials(config.client_display_name),
            is_online=True,
        )

        self._message_callbacks: list[Callable[[Message], None]] = []
        self._contact_callbacks: list[Callable[[User], None]] = []
        self._status_callbacks: list[Callable[[str, str], None]] = []
        self._presence_callbacks: list[Callable[[str, bool], None]] = []

        # Query response tracking (query_id -> (threading.Event, dict))
        self._pending_queries: dict[str, tuple[threading.Event, dict[str, Any]]] = {}
        self._query_lock = threading.Lock()

        self._client = TcpClient(
            host=config.server_ip,
            port=config.server_port,
            on_packet=self._handle_server_packet,
            on_status=self._handle_connection_status,
        )

    def _compute_initials(self, name: str) -> str:
        """Compute 1-2 character uppercase initials from a display name."""
        parts = name.strip().split()
        if not parts:
            return "??"
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    def start(self) -> None:
        """Start the background TCP connection."""
        self._client.start()

    def stop(self) -> None:
        """Stop socket worker and wake any waiting query callers."""
        self._client.stop()
        with self._query_lock:
            for event, _ in self._pending_queries.values():
                event.set()
            self._pending_queries.clear()

    def get_current_user(self) -> User:
        """Return the currently authenticated user."""
        return self._current_user

    def get_contacts(self) -> list[User]:
        """Return the list of contacts for the current user from SQLite cache."""
        return self.db.get_contacts()

    def get_messages(self, contact_id: str) -> list[Message]:
        """Return all messages for the specified contact conversation from SQLite cache."""
        return self.db.get_messages(contact_id)

    def send_message(self, recipient_id: str, content: str) -> Message:
        """Send a message to a recipient, save locally, and transmit over TCP."""
        cleaned = content.strip()
        if not cleaned:
            raise ValueError("Message content cannot be empty.")

        msg_id = str(uuid.uuid4()).replace("-", "")[:12]
        msg = Message(
            id=msg_id,
            sender_id=self._current_user.id,
            recipient_id=recipient_id,
            content=cleaned,
            timestamp=datetime.now(),
            is_outgoing=True,
        )

        # Save immediately to local SQLite cache
        self.db.save_message(msg)

        # Transmit over TCP (replaces sender_id with receiver_id)
        packet = build_send_message(
            message_id=msg.id,
            receiver_id=recipient_id,
            content=cleaned,
        )
        self._client.send_packet(packet)

        return msg

    def query_user(self, username: str, timeout: float = 5.0) -> User | None:
        """Query remote server over TCP to check if username exists."""
        clean_user = username.strip().lstrip("@")
        if not clean_user or timeout <= 0 or not self._client.is_connected():
            return None

        query_id = str(uuid.uuid4()).replace("-", "")[:8]
        event = threading.Event()
        result_holder: dict[str, Any] = {}

        with self._query_lock:
            self._pending_queries[query_id] = (event, result_holder)

        packet = build_query_user(query_id=query_id, username=clean_user)
        self._client.send_packet(packet)

        # Wait for reply
        if not event.wait(timeout=timeout):
            with self._query_lock:
                self._pending_queries.pop(query_id, None)
            return None

        with self._query_lock:
            self._pending_queries.pop(query_id, None)

        if not result_holder.get("exists", False):
            return None

        raw_display = result_holder.get("display_name")
        display_name = str(raw_display) if raw_display else clean_user.capitalize()
        user_id = str(result_holder.get("user_id") or clean_user)
        user_name = str(result_holder.get("username") or clean_user)

        return User(
            id=user_id,
            username=user_name,
            display_name=display_name,
            avatar_initials=self._compute_initials(display_name),
            is_online=bool(result_holder.get("is_online", False)),
        )

    def add_contact(self, username: str, display_name: str) -> User:
        """Verify user via server query, save to SQLite, and dispatch callbacks."""
        clean_user = username.strip().lstrip("@")
        if not clean_user:
            raise ValueError("Username cannot be empty.")

        if not self._client.is_connected():
            raise ConnectionError("Cannot add contact: not connected to server.")

        # Query server
        remote_user = self.query_user(clean_user)
        if remote_user is None:
            raise ValueError(f"User '@{clean_user}' does not exist on server.")

        # Override display name if provided by user
        final_name = display_name.strip() if display_name.strip() else remote_user.display_name
        contact = User(
            id=remote_user.id,
            username=remote_user.username,
            display_name=final_name,
            avatar_initials=self._compute_initials(final_name),
            is_online=remote_user.is_online,
        )

        self.db.upsert_contact(contact)

        for cb in list(self._contact_callbacks):
            try:
                cb(contact)
            except Exception:
                pass

        return contact

    def subscribe_message_received(self, callback: Callable[[Message], None]) -> None:
        """Subscribe a callback to be notified when a new incoming message is received."""
        self._message_callbacks.append(callback)

    def subscribe_contact_added(self, callback: Callable[[User], None]) -> None:
        """Subscribe a callback to be notified when a new contact is added."""
        self._contact_callbacks.append(callback)

    def subscribe_connection_status(self, callback: Callable[[str, str], None]) -> None:
        """Subscribe a callback to be notified of connection status transitions."""
        self._status_callbacks.append(callback)

    def subscribe_presence_updated(self, callback: Callable[[str, bool], None]) -> None:
        """Subscribe a callback to be notified when a contact presence status changes."""
        self._presence_callbacks.append(callback)

    def _handle_connection_status(self, status: str, detail: str) -> None:
        """Handle socket state changes and perform initial identify handshake upon connection."""
        if status == "CONNECTED":
            # Send identify handshake on connect
            ident = build_identify(
                user_id=self._current_user.id,
                username=self._current_user.username,
                display_name=self._current_user.display_name,
            )
            self._client.send_packet(ident)

        for cb in list(self._status_callbacks):
            try:
                cb(status, detail)
            except Exception:
                pass

    def _handle_server_packet(self, packet: dict[str, Any]) -> None:
        """Dispatch incoming parsed NDJSON packets according to action."""
        action = packet.get("action")

        if action == "query_user_response":
            qid = packet.get("query_id")
            with self._query_lock:
                entry = self._pending_queries.get(qid)
                if entry:
                    event, holder = entry
                    holder.update(packet)
                    event.set()

        elif action == "message":
            # Incoming chat message from remote server
            msg_id = packet.get("message_id", str(uuid.uuid4()).replace("-", "")[:8])
            sender_id = packet.get("sender_id", "unknown")
            recipient_id = packet.get("receiver_id") or packet.get("recipient_id") or self._current_user.id
            content = packet.get("content", "")
            ts_str = packet.get("timestamp")
            try:
                ts = datetime.fromisoformat(ts_str) if ts_str else datetime.now()
            except Exception:
                ts = datetime.now()

            msg = Message(
                id=msg_id,
                sender_id=sender_id,
                recipient_id=recipient_id,
                content=content,
                timestamp=ts,
                is_outgoing=False,
            )
            self.db.save_message(msg)

            for cb in list(self._message_callbacks):
                try:
                    cb(msg)
                except Exception:
                    pass

        elif action == "history_sync":
            # Sync historical messages from server
            raw_messages = packet.get("messages", [])
            parsed_messages: list[Message] = []
            if isinstance(raw_messages, list):
                for item in raw_messages:
                    if not isinstance(item, dict):
                        continue
                    m_id = str(item.get("message_id") or uuid.uuid4().hex[:8])
                    s_id = str(item.get("sender_id", ""))
                    r_id = str(item.get("receiver_id") or item.get("recipient_id") or self._current_user.id)
                    cnt = str(item.get("content", ""))
                    is_out = (s_id == self._current_user.id)
                    ts_val = item.get("timestamp")
                    try:
                        t_stamp = datetime.fromisoformat(ts_val) if ts_val else datetime.now()
                    except Exception:
                        t_stamp = datetime.now()
                    parsed_messages.append(Message(m_id, s_id, r_id, cnt, t_stamp, is_out))

            self.db.merge_history(parsed_messages)

        elif action == "user_status":
            u_id = packet.get("user_id")
            online = bool(packet.get("is_online", False))
            if u_id:
                self.db.update_contact_status(u_id, online)
                for cb in list(self._presence_callbacks):
                    try:
                        cb(u_id, online)
                    except Exception:
                        pass
