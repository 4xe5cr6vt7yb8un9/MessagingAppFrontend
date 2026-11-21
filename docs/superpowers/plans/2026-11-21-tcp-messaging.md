# Real TCP Messaging & Local SQLite Cache — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace dummy in-memory messaging functions with a persistent, continuous TCP socket client communicating with a remote server via newline-delimited JSON (NDJSON), backed by an offline-first local SQLite database cache, environment-based configuration (`.env`), remote user queries, initial chat history sync, and live connection health status.

**Architecture:** Background Socket Engine (`network/tcp_client.py`) + SQLite Cache Repository (`cache/database.py`) + Service Adapter (`services/tcp_service.py`) implementing `MessagingServiceProtocol`. Decoupled architecture preserves the existing CustomTkinter GUI layout while streaming real-time messages and query results over TCP.

**Tech Stack:** Python 3.14+, `customtkinter`, `pillow`, `pytest`, `python-dotenv`, standard library `socket`, `threading`, `queue`, `sqlite3`, `json`.

**Spec:** [`docs/superpowers/specs/2026-11-21-tcp-messaging-design.md`](file:///d:/Sync/Projects/MessagingAppFrontend/docs/superpowers/specs/2026-11-21-tcp-messaging-design.md)

## Global Constraints
- Naming & Code Quality: Strictly adhere to PEP 8, `python-patterns` (type hints everywhere, context managers, explicit exception handling), and `coding-standards`.
- Framing: All TCP messages use Newline-Delimited JSON (NDJSON) with UTF-8 encoding.
- Payload Convention: Outgoing chat messages MUST replace `sender_id` with `receiver_id` (`{"action": "message", "message_id": "...", "receiver_id": "...", "content": "..."}`).
- Offline-First / Instant UI: Local SQLite cache loads contacts and messages immediately before/during socket connection.
- Thread Safety: Socket operations run strictly on background threads; UI updates are marshaled to the Tkinter main thread using `self.after(0, ...)`.
- Immutability: Entities `User` and `Message` remain frozen dataclasses.

---

## Tasks

### Task 1: Environment Configuration & Dependencies (`.env`, `config.py`)

**Files:**
- Modify: `requirements.txt`
- Create: `.env.example`
- Create: `.env`
- Create: `src/messaging_app/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: `python-dotenv`, standard library `os`, `pathlib`.
- Produces: `AppConfig(server_ip: str, server_port: int, client_user_id: str, client_username: str, client_display_name: str, local_db_path: Path)` with `AppConfig.from_env()`.

- [ ] **Step 1: Update requirements.txt and install python-dotenv**

Update `requirements.txt`:
```text
customtkinter>=6.0.0
pillow>=10.0.0
pytest>=7.4.0
python-dotenv>=1.0.0
```

Run: `python -m pip install -r requirements.txt`  
Expected: Successfully installed `python-dotenv`.

- [ ] **Step 2: Create .env.example and .env**

Create `.env.example`:
```env
SERVER_IP=127.0.0.1
SERVER_PORT=9000
CLIENT_USER_ID=user_101
CLIENT_USERNAME=alice
CLIENT_DISPLAY_NAME=Alice Smith
LOCAL_DB_PATH=data/chat_cache.db
```

Copy `.env.example` to `.env`.

- [ ] **Step 3: Write failing unit test for AppConfig**

Write `tests/test_config.py`:
```python
from pathlib import Path
import os
import pytest
from messaging_app.config import AppConfig

def test_config_defaults(tmp_path: Path):
    empty_env = tmp_path / ".empty_env"
    empty_env.write_text("", encoding="utf-8")
    
    # Temporarily clear env vars
    old_env = {k: os.environ.pop(k, None) for k in [
        "SERVER_IP", "SERVER_PORT", "CLIENT_USER_ID", 
        "CLIENT_USERNAME", "CLIENT_DISPLAY_NAME", "LOCAL_DB_PATH"
    ]}
    try:
        config = AppConfig.from_env(env_path=empty_env)
        assert config.server_ip == "127.0.0.1"
        assert config.server_port == 9000
        assert config.client_user_id == "user_me"
        assert config.client_username == "me"
        assert config.client_display_name == "You"
        assert config.local_db_path == Path("data/chat_cache.db")
    finally:
        for k, v in old_env.items():
            if v is not None:
                os.environ[k] = v

def test_config_custom_values(tmp_path: Path):
    custom_env = tmp_path / ".custom_env"
    custom_env.write_text(
        "SERVER_IP=192.168.1.50\n"
        "SERVER_PORT=8080\n"
        "CLIENT_USER_ID=user_charlie\n"
        "CLIENT_USERNAME=charlie\n"
        "CLIENT_DISPLAY_NAME=Charlie Brown\n"
        "LOCAL_DB_PATH=data/custom.db\n",
        encoding="utf-8"
    )
    config = AppConfig.from_env(env_path=custom_env)
    assert config.server_ip == "192.168.1.50"
    assert config.server_port == 8080
    assert config.client_user_id == "user_charlie"
    assert config.client_username == "charlie"
    assert config.client_display_name == "Charlie Brown"
    assert config.local_db_path == Path("data/custom.db")
```

- [ ] **Step 4: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'messaging_app.config'`.

- [ ] **Step 5: Implement AppConfig in src/messaging_app/config.py**

Create `src/messaging_app/config.py`:
```python
"""Application configuration loader from .env file."""

from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    """Strongly typed application configuration settings."""

    server_ip: str
    server_port: int
    client_user_id: str
    client_username: str
    client_display_name: str
    local_db_path: Path

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> "AppConfig":
        """Load configuration from .env or environment variables with sane defaults."""
        if env_path is not None:
            if env_path.exists():
                load_dotenv(env_path, override=True)
        else:
            load_dotenv(override=False)

        server_port_str = os.getenv("SERVER_PORT", "9000")
        try:
            server_port = int(server_port_str)
        except ValueError:
            server_port = 9000

        return cls(
            server_ip=os.getenv("SERVER_IP", "127.0.0.1"),
            server_port=server_port,
            client_user_id=os.getenv("CLIENT_USER_ID", "user_me"),
            client_username=os.getenv("CLIENT_USERNAME", "me"),
            client_display_name=os.getenv("CLIENT_DISPLAY_NAME", "You"),
            local_db_path=Path(os.getenv("LOCAL_DB_PATH", "data/chat_cache.db")),
        )
```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`  
Expected: PASS (2 passed).

- [ ] **Step 7: Commit**

```bash
git add requirements.txt .env.example src/messaging_app/config.py tests/test_config.py
git commit -m "feat(config): add AppConfig and .env loader with python-dotenv"
```

---

### Task 2: Local SQLite Cache Layer (`cache/database.py`)

**Files:**
- Create: `src/messaging_app/cache/__init__.py`
- Create: `src/messaging_app/cache/database.py`
- Test: `tests/test_cache.py`

**Interfaces:**
- Consumes: `messaging_app.models.user.User`, `messaging_app.models.message.Message`, standard library `sqlite3`.
- Produces: `DatabaseCache(db_path: Path | str)`:
  - `save_message(message: Message) -> None`
  - `get_messages(contact_id: str) -> list[Message]`
  - `merge_history(messages: list[Message]) -> tuple[int, int]` (returns `(new_count, duplicate_count)`)
  - `upsert_contact(user: User) -> None`
  - `get_contacts() -> list[User]`
  - `update_contact_status(user_id: str, is_online: bool) -> None`

- [ ] **Step 1: Write the failing tests for DatabaseCache**

Write `tests/test_cache.py`:
```python
from datetime import datetime
from pathlib import Path
import pytest
from messaging_app.cache.database import DatabaseCache
from messaging_app.models.message import Message
from messaging_app.models.user import User

@pytest.fixture
def db_cache(tmp_path: Path) -> DatabaseCache:
    db_file = tmp_path / "test_chat.db"
    return DatabaseCache(db_file)

def test_save_and_get_messages(db_cache: DatabaseCache):
    msg1 = Message("m1", "alice", "me", "Hello!", datetime(2026, 11, 21, 10, 0), False)
    msg2 = Message("m2", "me", "alice", "Hi Alice!", datetime(2026, 11, 21, 10, 1), True)
    
    db_cache.save_message(msg1)
    db_cache.save_message(msg2)

    alice_history = db_cache.get_messages("alice")
    assert len(alice_history) == 2
    assert alice_history[0].id == "m1"
    assert alice_history[0].is_outgoing is False
    assert alice_history[1].id == "m2"
    assert alice_history[1].is_outgoing is True

def test_merge_history_deduplication(db_cache: DatabaseCache):
    existing = Message("m1", "bob", "me", "First message", datetime(2026, 11, 20, 12, 0), False)
    db_cache.save_message(existing)

    server_sync = [
        Message("m1", "bob", "me", "First message", datetime(2026, 11, 20, 12, 0), False),
        Message("m2", "bob", "me", "Second message", datetime(2026, 11, 20, 12, 5), False),
    ]

    new_count, dup_count = db_cache.merge_history(server_sync)
    assert new_count == 1
    assert dup_count == 1

    bob_history = db_cache.get_messages("bob")
    assert len(bob_history) == 2

def test_upsert_and_get_contacts(db_cache: DatabaseCache):
    alice = User("alice", "alice", "Alice Smith", "AS", True)
    db_cache.upsert_contact(alice)

    contacts = db_cache.get_contacts()
    assert len(contacts) == 1
    assert contacts[0].username == "alice"
    assert contacts[0].is_online is True

    # Update online status
    db_cache.update_contact_status("alice", False)
    updated = db_cache.get_contacts()
    assert updated[0].is_online is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cache.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'messaging_app.cache'`.

- [ ] **Step 3: Implement DatabaseCache**

Create `src/messaging_app/cache/__init__.py`:
```python
from messaging_app.cache.database import DatabaseCache

__all__ = ["DatabaseCache"]
```

Create `src/messaging_app/cache/database.py`:
```python
"""Local SQLite database cache for persistent offline chat history and contacts."""

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

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._lock, self._get_connection() as conn:
            conn.executescript("""
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
            """)

    def save_message(self, message: Message) -> None:
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
        with self._lock, self._get_connection() as conn:
            conn.execute(
                "UPDATE contacts SET is_online = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (1 if is_online else 0, user_id),
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_cache.py -v`  
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add src/messaging_app/cache/ tests/test_cache.py
git commit -m "feat(cache): implement DatabaseCache SQLite local history repository"
```

---

### Task 3: Wire Protocol Framing & Packet Serialization (`network/protocol_frames.py`)

**Files:**
- Create: `src/messaging_app/network/__init__.py`
- Create: `src/messaging_app/network/protocol_frames.py`
- Test: `tests/test_protocol_frames.py`

**Interfaces:**
- Consumes: Standard library `json`.
- Produces:
  - `encode_packet(data: dict) -> bytes` (appends `\n`)
  - `decode_lines(buffer: bytes) -> tuple[list[dict], bytes]` (parses full JSON objects, returns incomplete trailing bytes)
  - Builders: `build_identify(...)`, `build_send_message(...)`, `build_query_user(...)`

- [ ] **Step 1: Write failing unit tests for protocol frames**

Write `tests/test_protocol_frames.py`:
```python
import json
import pytest
from messaging_app.network.protocol_frames import (
    encode_packet,
    decode_lines,
    build_identify,
    build_send_message,
    build_query_user,
)

def test_encode_packet():
    data = {"action": "identify", "user_id": "u1"}
    encoded = encode_packet(data)
    assert encoded.endswith(b"\n")
    decoded = json.loads(encoded.decode("utf-8").strip())
    assert decoded["action"] == "identify"
    assert decoded["user_id"] == "u1"

def test_decode_lines_complete_and_partial():
    chunk1 = b'{"action": "ping"}\n{"action": "message", "content": "hi"}\n{"action": "part'
    packets, remaining = decode_lines(chunk1)
    assert len(packets) == 2
    assert packets[0]["action"] == "ping"
    assert packets[1]["content"] == "hi"
    assert remaining == b'{"action": "part'

    chunk2 = remaining + b'ial_done"}\n'
    packets2, remaining2 = decode_lines(chunk2)
    assert len(packets2) == 1
    assert packets2[0]["action"] == "partial_done"
    assert remaining2 == b""

def test_build_send_message_uses_receiver_id():
    packet = build_send_message(message_id="m123", receiver_id="user_bob", content="Hello!")
    assert packet["action"] == "message"
    assert packet["message_id"] == "m123"
    assert packet["receiver_id"] == "user_bob"
    assert "sender_id" not in packet
    assert packet["content"] == "Hello!"

def test_build_identify_and_query():
    ident = build_identify("u1", "alice", "Alice Smith")
    assert ident["action"] == "identify"
    assert ident["username"] == "alice"

    qry = build_query_user("q1", "bob")
    assert qry["action"] == "query_user"
    assert qry["query_id"] == "q1"
    assert qry["username"] == "bob"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_protocol_frames.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'messaging_app.network'`.

- [ ] **Step 3: Implement protocol_frames.py**

Create `src/messaging_app/network/__init__.py`:
```python
"""Networking package for persistent TCP communication."""
```

Create `src/messaging_app/network/protocol_frames.py`:
```python
"""Encoding, decoding, and builders for Newline-Delimited JSON (NDJSON) packets."""

import json
from typing import Any


def encode_packet(payload: dict[str, Any]) -> bytes:
    """Serialize dictionary payload to UTF-8 encoded bytes terminated by newline."""
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"


def decode_lines(buffer: bytes) -> tuple[list[dict[str, Any]], bytes]:
    """Parse newline-delimited chunks into JSON dictionaries, returning trailing remainder."""
    packets: list[dict[str, Any]] = []
    lines = buffer.split(b"\n")
    # The last element after split is either empty (if buffer ended in \n) or incomplete
    remainder = lines[-1]

    for line in lines[:-1]:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            parsed = json.loads(stripped.decode("utf-8"))
            if isinstance(parsed, dict):
                packets.append(parsed)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

    return packets, remainder


def build_identify(user_id: str, username: str, display_name: str) -> dict[str, Any]:
    """Build connection handshake packet."""
    return {
        "action": "identify",
        "user_id": user_id,
        "username": username,
        "display_name": display_name,
    }


def build_send_message(message_id: str, receiver_id: str, content: str) -> dict[str, Any]:
    """Build outgoing chat message packet replacing sender_id with receiver_id."""
    return {
        "action": "message",
        "message_id": message_id,
        "receiver_id": receiver_id,
        "content": content,
    }


def build_query_user(query_id: str, username: str) -> dict[str, Any]:
    """Build remote user query request packet."""
    return {
        "action": "query_user",
        "query_id": query_id,
        "username": username,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_protocol_frames.py -v`  
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add src/messaging_app/network/ tests/test_protocol_frames.py
git commit -m "feat(network): implement NDJSON packet encoding, decoding, and builders"
```

---

### Task 4: Persistent TCP Socket Client Engine (`network/tcp_client.py`)

**Files:**
- Create: `src/messaging_app/network/tcp_client.py`
- Test: `tests/test_tcp_client.py`

**Interfaces:**
- Consumes: `protocol_frames`, standard library `socket`, `threading`, `queue`, `select`.
- Produces: `TcpClient(host: str, port: int, on_packet: Callable[[dict], None], on_status: Callable[[str, str], None])`:
  - `start() -> None`
  - `stop() -> None`
  - `send_packet(packet: dict) -> None`
  - `is_connected() -> bool`

- [ ] **Step 1: Write unit tests with a local mock TCP server fixture**

Write `tests/test_tcp_client.py`:
```python
import socket
import threading
import time
import pytest
from messaging_app.network.tcp_client import TcpClient
from messaging_app.network.protocol_frames import encode_packet

@pytest.fixture
def mock_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(("127.0.0.1", 0))
    server_sock.listen(5)
    host, port = server_sock.getsockname()
    stop_event = threading.Event()
    clients = []

    def run_server():
        server_sock.settimeout(0.2)
        while not stop_event.is_set():
            try:
                conn, _ = server_sock.accept()
                clients.append(conn)
            except socket.timeout:
                continue

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    yield host, port, clients
    stop_event.set()
    thread.join(timeout=1.0)
    for c in clients:
        try:
            c.close()
        except Exception:
            pass
    server_sock.close()

def test_tcp_client_connect_and_exchange(mock_server):
    host, port, clients = mock_server
    received_packets = []
    statuses = []

    client = TcpClient(
        host=host,
        port=port,
        on_packet=lambda p: received_packets.append(p),
        on_status=lambda s, d: statuses.append(s),
        reconnect_interval=0.1,
    )
    client.start()

    # Wait for connection
    time.sleep(0.3)
    assert client.is_connected() is True
    assert "CONNECTED" in statuses
    assert len(clients) >= 1

    # Send from server to client
    server_conn = clients[0]
    server_conn.sendall(encode_packet({"action": "welcome", "text": "hello"}))
    time.sleep(0.2)
    assert len(received_packets) >= 1
    assert received_packets[0]["action"] == "welcome"

    client.stop()
    time.sleep(0.2)
    assert client.is_connected() is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tcp_client.py -v`  
Expected: FAIL with `ImportError: cannot import name 'TcpClient'`.

- [ ] **Step 3: Implement TcpClient in src/messaging_app/network/tcp_client.py**

Create `src/messaging_app/network/tcp_client.py`:
```python
"""Persistent TCP client socket engine with auto-reconnection and thread-safe queue."""

import queue
import select
import socket
import threading
import time
from typing import Any, Callable
from messaging_app.network.protocol_frames import decode_lines, encode_packet


class TcpClient:
    """Manages continuous TCP connection with a remote server in a background thread."""

    def __init__(
        self,
        host: str,
        port: int,
        on_packet: Callable[[dict[str, Any]], None],
        on_status: Callable[[str, str], None],
        reconnect_interval: float = 2.0,
    ) -> None:
        self.host = host
        self.port = port
        self.on_packet = on_packet
        self.on_status = on_status
        self.reconnect_interval = reconnect_interval

        self._send_queue: queue.Queue[dict[str, Any]] = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._connected = False
        self._sock: socket.socket | None = None

    def is_connected(self) -> bool:
        return self._connected

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="TcpClientThread")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._sock:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
        self._connected = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def send_packet(self, packet: dict[str, Any]) -> None:
        """Enqueue packet for transmission over the socket."""
        self._send_queue.put(packet)

    def _set_status(self, status: str, detail: str = "") -> None:
        self.on_status(status, detail)

    def _run_loop(self) -> None:
        backoff = self.reconnect_interval

        while not self._stop_event.is_set():
            self._set_status("CONNECTING", f"{self.host}:{self.port}")
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(4.0)
                sock.connect((self.host, self.port))
                sock.setblocking(False)
                self._sock = sock
                self._connected = True
                backoff = self.reconnect_interval
                self._set_status("CONNECTED", f"{self.host}:{self.port}")

                self._handle_socket_session(sock)
            except (socket.error, OSError) as exc:
                self._connected = False
                self._sock = None
                if not self._stop_event.is_set():
                    self._set_status("RECONNECTING", str(exc))
                    time.sleep(backoff)
                    backoff = min(backoff * 1.5, 10.0)

        self._connected = False
        self._set_status("DISCONNECTED", "Client stopped")

    def _handle_socket_session(self, sock: socket.socket) -> None:
        buffer = b""

        while not self._stop_event.is_set() and self._connected:
            read_socks = [sock]
            write_socks = [sock] if not self._send_queue.empty() else []

            try:
                r_ready, w_ready, x_ready = select.select(read_socks, write_socks, read_socks, 0.2)
            except (select.error, OSError):
                break

            if x_ready:
                break

            # Process outgoing packets
            if w_ready and not self._send_queue.empty():
                try:
                    packet = self._send_queue.get_nowait()
                    data = encode_packet(packet)
                    sock.sendall(data)
                except queue.Empty:
                    pass
                except (socket.error, OSError):
                    break

            # Process incoming data
            if r_ready:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        # Server closed connection
                        break
                    buffer += chunk
                    packets, buffer = decode_lines(buffer)
                    for pkt in packets:
                        try:
                            self.on_packet(pkt)
                        except Exception:
                            pass
                except (socket.error, BlockingIOError):
                    pass
                except Exception:
                    break

        self._connected = False
        try:
            sock.close()
        except Exception:
            pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_tcp_client.py -v`  
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add src/messaging_app/network/tcp_client.py tests/test_tcp_client.py
git commit -m "feat(network): implement persistent TcpClient with reconnect and send queue"
```

---

### Task 5: TCP Messaging Service Implementation (`services/tcp_service.py`)

**Files:**
- Create: `src/messaging_app/services/tcp_service.py`
- Modify: `src/messaging_app/services/__init__.py`
- Test: `tests/test_tcp_service.py`

**Interfaces:**
- Consumes: `AppConfig`, `DatabaseCache`, `TcpClient`, `MessagingServiceProtocol`, `User`, `Message`.
- Produces: `TcpMessagingService(config: AppConfig, db_cache: DatabaseCache)` implementing `MessagingServiceProtocol`:
  - `start()`, `stop()`
  - `get_current_user() -> User`
  - `get_contacts() -> list[User]`
  - `get_messages(contact_id: str) -> list[Message]`
  - `send_message(recipient_id: str, content: str) -> Message`
  - `query_user(username: str, timeout: float = 5.0) -> Optional[User]`
  - `add_contact(username: str, display_name: str) -> User`
  - `subscribe_message_received(callback: Callable[[Message], None]) -> None`
  - `subscribe_contact_added(callback: Callable[[User], None]) -> None`
  - `subscribe_connection_status(callback: Callable[[str, str], None]) -> None`
  - `subscribe_presence_updated(callback: Callable[[str, bool], None]) -> None`

- [ ] **Step 1: Write integration tests for TcpMessagingService**

Write `tests/test_tcp_service.py`:
```python
import socket
import threading
import time
from pathlib import Path
import pytest
from messaging_app.config import AppConfig
from messaging_app.cache.database import DatabaseCache
from messaging_app.services.tcp_service import TcpMessagingService
from messaging_app.network.protocol_frames import decode_lines, encode_packet
from messaging_app.services.protocol import MessagingServiceProtocol

@pytest.fixture
def mock_messaging_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(("127.0.0.1", 0))
    server_sock.listen(5)
    host, port = server_sock.getsockname()
    stop_event = threading.Event()
    received_packets = []
    client_connections = []

    def handle_client(conn: socket.socket):
        buf = b""
        conn.settimeout(0.2)
        while not stop_event.is_set():
            try:
                data = conn.recv(2048)
                if not data:
                    break
                buf += data
                pkts, buf = decode_lines(buf)
                for p in pkts:
                    received_packets.append(p)
                    # Handle query_user
                    if p.get("action") == "query_user":
                        u = p.get("username")
                        exists = (u == "bob")
                        resp = {
                            "action": "query_user_response",
                            "query_id": p.get("query_id"),
                            "exists": exists,
                            "user_id": "user_bob" if exists else "",
                            "username": "bob" if exists else u,
                            "display_name": "Bob Martinez" if exists else "",
                            "is_online": True,
                        }
                        conn.sendall(encode_packet(resp))
            except socket.timeout:
                continue
            except Exception:
                break

    def run_server():
        server_sock.settimeout(0.2)
        while not stop_event.is_set():
            try:
                conn, _ = server_sock.accept()
                client_connections.append(conn)
                t = threading.Thread(target=handle_client, args=(conn,), daemon=True)
                t.start()
            except socket.timeout:
                continue

    t_srv = threading.Thread(target=run_server, daemon=True)
    t_srv.start()
    yield host, port, received_packets, client_connections
    stop_event.set()
    t_srv.join(timeout=1.0)
    for c in client_connections:
        try:
            c.close()
        except Exception:
            pass
    server_sock.close()

def test_service_protocol_and_lifecycle(tmp_path: Path, mock_messaging_server):
    host, port, server_pkts, server_conns = mock_messaging_server
    config = AppConfig(
        server_ip=host,
        server_port=port,
        client_user_id="user_alice",
        client_username="alice",
        client_display_name="Alice Smith",
        local_db_path=tmp_path / "cache.db",
    )
    db = DatabaseCache(config.local_db_path)
    service = TcpMessagingService(config, db)
    assert isinstance(service, MessagingServiceProtocol)

    service.start()
    time.sleep(0.4)

    # Verify identify handshake was sent to server
    assert any(p.get("action") == "identify" and p.get("username") == "alice" for p in server_pkts)

    # Test send message
    sent_msg = service.send_message("user_bob", "Hello Bob over TCP!")
    assert sent_msg.content == "Hello Bob over TCP!"
    assert sent_msg.is_outgoing is True

    time.sleep(0.2)
    # Verify outgoing packet replaced sender_id with receiver_id
    msg_pkts = [p for p in server_pkts if p.get("action") == "message"]
    assert len(msg_pkts) >= 1
    assert msg_pkts[0]["receiver_id"] == "user_bob"
    assert "sender_id" not in msg_pkts[0]

    # Test query user exists
    user_bob = service.query_user("bob")
    assert user_bob is not None
    assert user_bob.username == "bob"

    # Test query user not exists
    user_unknown = service.query_user("unknown_user")
    assert user_unknown is None

    service.stop()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_tcp_service.py -v`  
Expected: FAIL with `ImportError: cannot import name 'TcpMessagingService'`.

- [ ] **Step 3: Implement TcpMessagingService in src/messaging_app/services/tcp_service.py**

Create `src/messaging_app/services/tcp_service.py`:
```python
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
        """Stop socket worker."""
        self._client.stop()

    def get_current_user(self) -> User:
        return self._current_user

    def get_contacts(self) -> list[User]:
        return self.db.get_contacts()

    def get_messages(self, contact_id: str) -> list[Message]:
        return self.db.get_messages(contact_id)

    def send_message(self, recipient_id: str, content: str) -> Message:
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
        if not clean_user:
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

        return User(
            id=result_holder.get("user_id", clean_user),
            username=result_holder.get("username", clean_user),
            display_name=result_holder.get("display_name", clean_user.capitalize()),
            avatar_initials=self._compute_initials(result_holder.get("display_name", clean_user)),
            is_online=bool(result_holder.get("is_online", False)),
        )

    def add_contact(self, username: str, display_name: str) -> User:
        """Verify user via server query, save to SQLite, and dispatch callbacks."""
        clean_user = username.strip().lstrip("@")
        if not clean_user:
            raise ValueError("Username cannot be empty.")

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
        self._message_callbacks.append(callback)

    def subscribe_contact_added(self, callback: Callable[[User], None]) -> None:
        self._contact_callbacks.append(callback)

    def subscribe_connection_status(self, callback: Callable[[str, str], None]) -> None:
        self._status_callbacks.append(callback)

    def subscribe_presence_updated(self, callback: Callable[[str, bool], None]) -> None:
        self._presence_callbacks.append(callback)

    def _handle_connection_status(self, status: str, detail: str) -> None:
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
            msg_id = packet.get("message_id", str(uuid.uuid4())[:8])
            sender_id = packet.get("sender_id", "unknown")
            content = packet.get("content", "")
            ts_str = packet.get("timestamp")
            try:
                ts = datetime.fromisoformat(ts_str) if ts_str else datetime.now()
            except Exception:
                ts = datetime.now()

            msg = Message(
                id=msg_id,
                sender_id=sender_id,
                recipient_id=self._current_user.id,
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
            for item in raw_messages:
                m_id = item.get("message_id", str(uuid.uuid4())[:8])
                s_id = item.get("sender_id", "")
                r_id = item.get("receiver_id", self._current_user.id)
                cnt = item.get("content", "")
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
```

Update `src/messaging_app/services/__init__.py`:
```python
from messaging_app.services.protocol import MessagingServiceProtocol
from messaging_app.services.dummy_service import DummyMessagingService
from messaging_app.services.tcp_service import TcpMessagingService

__all__ = ["MessagingServiceProtocol", "DummyMessagingService", "TcpMessagingService"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_tcp_service.py -v`  
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add src/messaging_app/services/tcp_service.py src/messaging_app/services/__init__.py tests/test_tcp_service.py
git commit -m "feat(services): implement TcpMessagingService with SQLite cache and TCP networking"
```

---

### Task 6: UI Connection Indicator & Query-Based Contact Addition

**Files:**
- Modify: `src/messaging_app/ui/components/sidebar.py`
- Modify: `src/messaging_app/ui/components/add_user_modal.py`
- Modify: `src/messaging_app/ui/app.py`
- Test: `tests/test_ui_tcp_integration.py`

**Interfaces:**
- Consumes: `Sidebar`, `AddUserModal`, `MessagingApp`, `TcpMessagingService`.
- Produces: Live UI connection status pill in Sidebar, server existence validation in `AddUserModal`, real-time presence updates.

- [ ] **Step 1: Write UI integration test for connection status and presence**

Write `tests/test_ui_tcp_integration.py`:
```python
import customtkinter
import pytest
from messaging_app.models.user import User
from messaging_app.services.dummy_service import DummyMessagingService
from messaging_app.ui.app import MessagingApp

def test_sidebar_connection_status_update():
    root = customtkinter.CTk()
    service = DummyMessagingService()
    app = MessagingApp(service=service)

    # Check that status pill exists on sidebar
    assert hasattr(app.sidebar, "connection_pill")
    
    # Test setting connection status
    app.sidebar.set_connection_status("CONNECTED", "127.0.0.1:9000")
    assert "Connected" in app.sidebar.connection_pill.cget("text")
    
    app.sidebar.set_connection_status("RECONNECTING", "refused")
    assert "Reconnecting" in app.sidebar.connection_pill.cget("text")
    
    app.sidebar.set_connection_status("DISCONNECTED", "")
    assert "Disconnected" in app.sidebar.connection_pill.cget("text")

    app.destroy()
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_ui_tcp_integration.py -v`  
Expected: FAIL with `AssertionError: assert hasattr(app.sidebar, 'connection_pill')`.

- [ ] **Step 3: Update Sidebar with connection status pill**

In `src/messaging_app/ui/components/sidebar.py`:
Add `connection_pill` label directly under the header frame.
Implement `set_connection_status(self, status: str, detail: str = "")`:
- If `CONNECTED`: dot color `#10B981` (green), text `● Connected`
- If `RECONNECTING`: dot color `#F59E0B` (amber), text `○ Reconnecting...`
- Otherwise: dot color `#EF4444` (red), text `✕ Disconnected`

- [ ] **Step 4: Update AddUserModal with query-based feedback**

In `src/messaging_app/ui/components/add_user_modal.py`:
- Update `_handle_submit`: disable the Add Contact button while verifying, set text to *"Verifying..."*, call `on_submit()`, and re-enable on error.

- [ ] **Step 5: Update MessagingApp to wire connection and presence callbacks**

In `src/messaging_app/ui/app.py`:
- Check if service supports `subscribe_connection_status` and register callback:
  ```python
  if hasattr(self.service, "subscribe_connection_status"):
      self.service.subscribe_connection_status(
          lambda s, d: self.after(0, self.sidebar.set_connection_status, s, d)
      )
  ```
- Check if service supports `subscribe_presence_updated` and register callback to update contact dots:
  ```python
  if hasattr(self.service, "subscribe_presence_updated"):
      self.service.subscribe_presence_updated(
          lambda u_id, online: self.after(0, self._handle_presence_update_ui, u_id, online)
      )
  ```

- [ ] **Step 6: Run test to verify it passes**

Run: `pytest tests/test_ui_tcp_integration.py -v`  
Expected: PASS (1 passed).

- [ ] **Step 7: Commit**

```bash
git add src/messaging_app/ui/ tests/test_ui_tcp_integration.py
git commit -m "feat(ui): add connection status indicator and live presence handling"
```

---

### Task 7: Main Startup Integration, CLI & Full Verification Suite

**Files:**
- Modify: `src/messaging_app/main.py`
- Modify: `README.md`
- Test: All tests across the entire test suite.

**Interfaces:**
- Consumes: Complete project codebase.
- Produces: Fully wired production application defaulting to `TcpMessagingService` with `.env` parameters, clean graceful shutdown, and updated documentation.

- [ ] **Step 1: Update src/messaging_app/main.py**

Modify `src/messaging_app/main.py` to use `AppConfig.from_env()`, `DatabaseCache`, and `TcpMessagingService`:
```python
from messaging_app.config import AppConfig
from messaging_app.cache.database import DatabaseCache
from messaging_app.services.tcp_service import TcpMessagingService
from messaging_app.ui.app import MessagingApp

def main() -> None:
    if "--help" in sys.argv or "-h" in sys.argv:
        print("NexusChat - Real-Time TCP Messaging Application")
        print("\nUsage: python -m src.messaging_app.main [options]")
        print("\nConfiguration is read from .env file (see .env.example).")
        return

    config = AppConfig.from_env()
    db_cache = DatabaseCache(config.local_db_path)
    service = TcpMessagingService(config=config, db_cache=db_cache)
    service.start()

    app = MessagingApp(service=service)
    try:
        app.mainloop()
    finally:
        service.stop()
```

- [ ] **Step 2: Run the full test suite**

Run: `pytest -v`  
Expected: All tests pass (50+ tests).

- [ ] **Step 3: Update README.md**

Update `README.md` with:
- TCP architecture explanation
- `.env` configuration instructions
- Packet specification and JSON format documentation
- How to test and run the app

- [ ] **Step 4: Commit**

```bash
git add src/messaging_app/main.py README.md
git commit -m "feat: complete TCP messaging service integration and documentation"
```
