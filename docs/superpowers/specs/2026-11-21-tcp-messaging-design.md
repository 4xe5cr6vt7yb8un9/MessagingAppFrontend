# Real TCP Messaging & Local SQLite Cache — Design Specification

**Date:** 2026-11-21  
**Status:** Approved  
**Networking:** Persistent TCP Socket Client with Newline-Delimited JSON (NDJSON)  
**Configuration:** `.env` loaded via `python-dotenv`  
**Persistence:** Local SQLite Database Cache (`sqlite3`)  
**Architecture:** Background Socket Engine + Database Cache Repository + Service Adapter  

---

## 1. Overview & Objectives

This specification transitions the NexusChat application from dummy in-memory messaging to production-ready, real-time TCP messaging connected to a central remote server:
1. **Configuration (`.env`):** Defines remote server IP (`SERVER_IP`), port (`SERVER_PORT`), client identity (`CLIENT_USER_ID`, `CLIENT_USERNAME`, `CLIENT_DISPLAY_NAME`), and local database path (`LOCAL_DB_PATH`).
2. **Persistent TCP Connection:** Continuous socket connection managed on a dedicated background worker thread with automatic exponential backoff reconnection.
3. **JSON Framing:** Newline-Delimited JSON (NDJSON) where every message payload is terminated with `\n`.
4. **Message Payloads:**
   - Outgoing messages send `receiver_id`, `message_id`, and `content`.
   - Incoming messages receive `sender_id`, `message_id`, and `content`.
5. **User Query Functionality:** Request-response correlation over TCP to verify if a user exists, and retrieve their canonical username, display name, and online status.
6. **Local SQLite Caching & History Sync:**
   - Local chat history and contacts are stored in `data/chat_cache.db`.
   - On initial connection, client sends an `identify` handshake.
   - Server returns the user's historical chat messages (`history_sync`), which is compared and merged into the local SQLite cache deduplicated by `message_id`.
   - Real-time presence updates (`user_status`) update contact status dynamically in the UI.
7. **Connection State Feedback:** A live connection status pill in the sidebar header reflects socket health (Connected / Reconnecting / Disconnected).

---

## 2. Configuration & Environment (`.env`)

### 2.1 Schema & Environment Variables
The root `.env` (with template `.env.example`) defines:

```env
SERVER_IP=127.0.0.1
SERVER_PORT=9000
CLIENT_USER_ID=user_101
CLIENT_USERNAME=alice
CLIENT_DISPLAY_NAME=Alice Smith
LOCAL_DB_PATH=data/chat_cache.db
```

### 2.2 Configuration Loader (`src/messaging_app/config.py`)
```python
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

@dataclass(frozen=True)
class AppConfig:
    server_ip: str
    server_port: int
    client_user_id: str
    client_username: str
    client_display_name: str
    local_db_path: Path

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> "AppConfig":
        if env_path and env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()

        return cls(
            server_ip=os.getenv("SERVER_IP", "127.0.0.1"),
            server_port=int(os.getenv("SERVER_PORT", "9000")),
            client_user_id=os.getenv("CLIENT_USER_ID", "user_me"),
            client_username=os.getenv("CLIENT_USERNAME", "me"),
            client_display_name=os.getenv("CLIENT_DISPLAY_NAME", "You"),
            local_db_path=Path(os.getenv("LOCAL_DB_PATH", "data/chat_cache.db")),
        )
```

---

## 3. Local SQLite Cache Layer (`src/messaging_app/cache/`)

### 3.1 Schema (`database.py`)
Standard library `sqlite3` handles atomic local persistence:

```sql
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
    timestamp TIMESTAMP NOT NULL,
    is_outgoing INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation 
ON messages(sender_id, recipient_id, timestamp);
```

### 3.2 Cache Operations
* `get_contacts() -> list[User]`
* `upsert_contact(user: User) -> None`
* `get_messages(contact_id: str) -> list[Message]`
* `save_message(message: Message) -> None`
* `merge_history(server_messages: list[Message]) -> tuple[int, int]`:
  Inserts server messages using `INSERT OR IGNORE INTO messages ...` and returns `(new_count, duplicate_count)`.

---

## 4. TCP Wire Protocol & Packet Schemas (`src/messaging_app/network/`)

### 4.1 Framing
Every JSON packet is serialized to UTF-8 and terminated with `\n` (NDJSON). Incomplete chunks in `recv()` remain in the streaming buffer until the next `\n` arrives.

### 4.2 Packet Specifications

#### 1. Identity Handshake (Client → Server)
```json
{
  "action": "identify",
  "user_id": "user_101",
  "username": "alice",
  "display_name": "Alice Smith"
}
```

#### 2. Send Message (Client → Server)
*Replaces `sender_id` with `receiver_id`:*
```json
{
  "action": "message",
  "message_id": "msg_001_uuid",
  "receiver_id": "user_202",
  "content": "Hello Bob!"
}
```

#### 3. Receive Message (Server → Client)
```json
{
  "action": "message",
  "message_id": "msg_001_uuid",
  "sender_id": "user_202",
  "content": "Hello Bob!",
  "timestamp": "2026-11-21T11:24:00"
}
```

#### 4. Initial Chat History Sync (Server → Client)
```json
{
  "action": "history_sync",
  "messages": [
    {
      "message_id": "m_100",
      "sender_id": "user_202",
      "receiver_id": "user_101",
      "content": "Welcome to NexusChat!",
      "timestamp": "2026-11-20T12:00:00"
    }
  ]
}
```

#### 5. User Query Request (Client → Server)
```json
{
  "action": "query_user",
  "query_id": "q_uuid_123",
  "username": "bob"
}
```

#### 6. User Query Response (Server → Client)
```json
{
  "action": "query_user_response",
  "query_id": "q_uuid_123",
  "exists": true,
  "user_id": "user_202",
  "username": "bob",
  "display_name": "Bob Martinez",
  "is_online": true
}
```

#### 7. User Status Push Event (Server → Client)
```json
{
  "action": "user_status",
  "user_id": "user_202",
  "is_online": false
}
```

---

## 5. TCP Client Engine (`src/messaging_app/network/tcp_client.py`)

A robust, non-blocking socket loop running on a background daemon thread:
* **Outgoing Queue:** `queue.Queue[dict[str, Any]]` serialized to NDJSON.
* **Stream Buffer:** Decodes continuous chunks and slices by `\n`.
* **State Machine:** `DISCONNECTED` → `CONNECTING` → `CONNECTED` → `RECONNECTING`.
* **Automatic Reconnection:** Exponential backoff (1s, 2s, 4s, 8s, max 10s) upon socket disconnect or refused connection.
* **Callbacks:**
  - `on_packet_received(packet: dict[str, Any]) -> None`
  - `on_connection_status(status: str, detail: str) -> None`

---

## 6. Service Integration (`src/messaging_app/services/tcp_service.py`)

`TcpMessagingService` implements `MessagingServiceProtocol`:
1. **Initial Local Load:** Instantly reads contacts and conversation history from `DatabaseCache`.
2. **Socket Startup:** Starts `TcpClient`, sends `identify`.
3. **History Sync Processing:** On `history_sync`, merges messages into SQLite and notifies UI if active conversation has new messages.
4. **Message Dispatch:** `send_message()` stores to SQLite, queues outgoing packet, and returns `Message` for instant UI rendering.
5. **Query Handling:** `query_user(username: str, timeout: float)` blocks the calling thread using `threading.Event()` keyed by `query_id` and returns the resolved `User` or `None`.
6. **Contact Addition:** `add_contact()` invokes `query_user()` to verify the user exists on the remote server before saving to SQLite and notifying the UI.

---

## 7. UI Updates (`src/messaging_app/ui/`)

1. **Sidebar Connection Indicator:**
   A status pill added to the sidebar header showing connection health:
   - Green dot: `● Connected`
   - Amber dot: `○ Reconnecting...`
   - Red dot: `✕ Disconnected`
2. **Add User Modal Enhancement:**
   - Validates user existence with the server via `service.query_user()`.
   - Shows feedback if user is not found on the server.
3. **Dynamic Presence Updates:**
   - Online/offline dots update in real time when `user_status` events arrive.
