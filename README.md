# NexusChat — Modern Desktop Messaging Application

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/GUI-CustomTkinter-indigo.svg)](https://customtkinter.tomschimansky.com/)
[![Protocol](https://img.shields.io/badge/Protocol-TCP%20%2F%20NDJSON-orange.svg)]()
[![Database](https://img.shields.io/badge/Cache-SQLite-lightgrey.svg)]()
[![Tests](https://img.shields.io/badge/Tests-86%20Passing-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-gray.svg)]()

**NexusChat** is a production-ready, responsive desktop messaging application built in Python using **CustomTkinter**, **SQLite**, and standard library **TCP sockets**. It delivers real-time bidirectional communication over a newline-delimited JSON (NDJSON) wire protocol, backed by a persistent local SQLite cache for instant offline startup and history deduplication.

---

## Key Highlights

- **Real-Time TCP Networking**: Robust background socket client with automated exponential backoff reconnection, thread-safe message queues, and graceful shutdown.
- **Persistent Local SQLite Cache**: Instant application startup loading contacts and message history from disk before network connection is established; seamless server history sync and deduplication.
- **Wire Protocol & Schema Compliance**: Fully documented NDJSON wire protocol handling `identify`, `message` (outgoing `receiver_id`, incoming `sender_id`), `query_user`, `query_user_response`, `history_sync`, and live `user_status` presence broadcasts.
- **Live Connection & Presence Indicators**: Real-time status pill (`● Connected`, `○ Reconnecting...`, `✕ Disconnected`) and contact presence dots (`● Online` / `○ Offline`) in both the sidebar and active chat header.
- **Responsive Two-Column CustomTkinter UI**: Fixed 300px sidebar with live search, theme toggling, and contact management; fluid chat canvas with speech bubbles and composer.
- **Thread-Safe Architecture**: Asynchronous background network events dispatched safely to the UI thread via `winfo_exists()`-guarded `after()` scheduling.
- **Configurable Environment**: Clean 12-factor configuration via `.env` file or environment variables with typed defaults and fallback parsing.

---

## Architecture & Directory Layout

NexusChat follows a decoupled **Model-View-Service-Cache-Network** architecture. The presentation layer depends only on `MessagingServiceProtocol`, completely isolating GUI logic from network transport and storage implementations.

```
MessagingAppFrontend/
├── data/                               # Default directory for local SQLite databases
├── src/
│   └── messaging_app/
│       ├── __init__.py
│       ├── main.py                     # Application entry point & CLI parser
│       ├── config.py                   # AppConfig loaded from environment / .env
│       ├── models/                     # Immutable data entities (@dataclass(frozen=True))
│       │   ├── __init__.py
│       │   ├── user.py                 # User (id, username, display_name, is_online, ...)
│       │   └── message.py              # Message (id, sender_id, recipient_id, content, ...)
│       ├── cache/                      # Persistent offline storage
│       │   ├── __init__.py
│       │   └── database.py             # DatabaseCache (SQLite contacts & messages)
│       ├── network/                    # Low-level socket communication
│       │   ├── __init__.py
│       │   ├── protocol_frames.py      # NDJSON encoder/decoder & packet builders
│       │   └── tcp_client.py           # Threaded TCP socket client with auto-reconnect
│       ├── services/                   # Business logic and coordination
│       │   ├── __init__.py
│       │   ├── protocol.py             # MessagingServiceProtocol interface
│       │   ├── tcp_service.py          # Production TCP messaging service with SQLite cache
│       │   └── dummy_service.py        # In-memory simulation service for GUI tests
│       └── ui/                         # CustomTkinter graphical interface
│           ├── __init__.py
│           ├── app.py                  # Root MessagingApp window & event dispatcher
│           ├── theme.py                # Design tokens, color palettes & radii
│           ├── icons.py                # Lucide SVG rasterizer and CTkImage loader
│           ├── assets/
│           │   └── icons/              # Embedded vector SVG icons
│           └── components/             # Reusable UI widgets
│               ├── __init__.py
│               ├── sidebar.py          # User header, connection status pill, search & contact list
│               ├── chat_area.py        # Active contact header, presence, message stream & composer
│               ├── message_bubble.py   # Speech bubble with avatar initials & timestamps
│               └── add_user_modal.py   # Contact search & addition modal with server verification
├── tests/                              # Comprehensive test suite (86 tests)
│   ├── conftest.py                     # Root test configuration & Windows Tk cooldown
│   ├── test_add_user_modal.py
│   ├── test_app_integration.py
│   ├── test_cache.py                   # SQLite cache & deduplication tests
│   ├── test_chat_area.py
│   ├── test_config.py                  # AppConfig validation & fallback tests
│   ├── test_environment.py
│   ├── test_main.py                    # Entry point CLI & lifecycle orchestration tests
│   ├── test_message_bubble.py
│   ├── test_models.py
│   ├── test_protocol_frames.py         # NDJSON framing & schema tests
│   ├── test_services.py
│   ├── test_sidebar.py
│   ├── test_tcp_client.py              # Socket connection, reconnect & queue tests
│   ├── test_tcp_service.py             # TcpMessagingService orchestration tests
│   ├── test_theme_and_icons.py
│   └── test_ui_tcp_integration.py      # UI live presence & connection status tests
├── requirements.txt                    # Project dependencies
└── README.md                           # Documentation
```

### Component Interaction Flow

```
[ User Interaction ]
         │
         ▼
[ CustomTkinter UI (MessagingApp) ]
         │
         │  service.send_message(recipient_id, text)
         ▼
[ TcpMessagingService ]
     ├── 1. Persist to DatabaseCache (SQLite) ────────► [ data/chat.db ]
     └── 2. Enqueue packet to TcpClient ──────────────► [ Background Worker Thread ]
                                                              │
                                                              │  NDJSON over TCP Socket
                                                              ▼
                                                      [ Remote TCP Server ]
                                                              │
                                                              ▼
                                                      [ Incoming Packets ]
                                                              │
     ┌────────────────────────────────────────────────────────┘
     ▼
[ TcpClient on_packet callback ]
     │
     ▼
[ TcpMessagingService._handle_server_packet ]
     ├── message: Save to SQLite Cache ───────────────► [ notify message subscriber ]
     ├── history_sync: Merge & Deduplicate ───────────► [ bulk upsert to SQLite ]
     ├── user_status: Update Presence ────────────────► [ notify presence subscriber ]
     └── query_user_response: Unblock waiting add ───► [ return User to UI modal ]
                                                              │
                                                              ▼
                                               [ root.after(0, update_ui) ]
                                                              │
                                                              ▼
                                               [ Thread-Safe UI Update ]
```

---

## Configuration & Environment Variables

NexusChat is configured via environment variables or a local `.env` file in the root directory.

### Configuration Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `SERVER_IP` | `str` | `127.0.0.1` | Remote TCP server IP address or hostname |
| `SERVER_PORT` | `int` | `9000` | Remote TCP server port number (1-65535) |
| `CLIENT_USER_ID` | `str` | `user-001` | Unique identifier for the local authenticated user |
| `CLIENT_USERNAME` | `str` | `aiden` | Handle/username for the local user |
| `CLIENT_DISPLAY_NAME`| `str` | `Aiden Pear` | Full display name for the local user |
| `LOCAL_DB_PATH` | `str` | `data/chat.db` | Filesystem path to the local SQLite database cache |

### Example `.env` File

Create a `.env` file in the project root:

```ini
# Server Connection
SERVER_IP=127.0.0.1
SERVER_PORT=9000

# Client Identity
CLIENT_USER_ID=user-001
CLIENT_USERNAME=aiden
CLIENT_DISPLAY_NAME=Aiden Pear

# Storage
LOCAL_DB_PATH=data/chat.db
```

---

## Wire Protocol Specification

The client communicates with the server over a single persistent TCP socket using **Newline-Delimited JSON (NDJSON)**. Every message is a single-line JSON object encoded as UTF-8, terminated by `\n` (`0x0A`).

### 1. Connection Handshake: `identify`

Immediately upon establishing a socket connection, the client transmits an `identify` packet declaring its credentials:

**Client → Server:**
```json
{
  "action": "identify",
  "user_id": "user-001",
  "username": "aiden",
  "display_name": "Aiden Pear"
}
```

### 2. Chat Messaging: `message`

The protocol uses asymmetric fields between outgoing and incoming messages:

**Outgoing (Client → Server):**
The client designates the target user using `receiver_id`:
```json
{
  "action": "message",
  "receiver_id": "user-002",
  "content": "Hello, Bob!"
}
```

**Incoming (Server → Client):**
The server delivers messages identifying the sender via `sender_id`:
```json
{
  "action": "message",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "sender_id": "user-002",
  "content": "Hey Aiden, received loud and clear!",
  "timestamp": "2026-11-21T14:30:00"
}
```

### 3. Contact Lookup: `query_user` & `query_user_response`

When adding a contact via the UI modal, the client queries the server to verify that the username exists before adding it to the local roster:

**Client → Server:**
```json
{
  "action": "query_user",
  "username": "sarah_c",
  "query_id": "c3d944e8-8b2b-4fa8-b21a-4632ef39b2cd"
}
```

**Server → Client (User Exists):**
```json
{
  "action": "query_user_response",
  "query_id": "c3d944e8-8b2b-4fa8-b21a-4632ef39b2cd",
  "exists": true,
  "user": {
    "id": "user-003",
    "username": "sarah_c",
    "display_name": "Sarah Connor",
    "is_online": true
  }
}
```

**Server → Client (User Not Found):**
```json
{
  "action": "query_user_response",
  "query_id": "c3d944e8-8b2b-4fa8-b21a-4632ef39b2cd",
  "exists": false,
  "user": null
}
```
*Note: If the client is disconnected when an add request is made, `add_contact` fails fast with an immediate validation error without blocking.*

### 4. History Synchronization: `history_sync`

Upon successful identification, the server transmits historical messages for synchronization:

**Server → Client:**
```json
{
  "action": "history_sync",
  "messages": [
    {
      "id": "msg-001",
      "sender_id": "user-002",
      "receiver_id": "user-001",
      "content": "Previous conversation message",
      "timestamp": "2026-11-21T10:00:00"
    }
  ]
}
```

### 5. Live Presence Updates: `user_status`

The server broadcasts online status transitions for connected contacts:

**Server → Client:**
```json
{
  "action": "user_status",
  "user_id": "user-002",
  "is_online": true
}
```

---

## SQLite Local Caching & Sync Deduplication

NexusChat uses `sqlite3` to guarantee offline availability and fast application boot times.

### Database Schema

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

CREATE INDEX IF NOT EXISTS idx_messages_contact
ON messages(sender_id, recipient_id, timestamp);
```

### Deduplication Logic

When receiving historical messages via `history_sync` or individual incoming messages:
1. `DatabaseCache.merge_history()` uses `INSERT OR REPLACE INTO messages` parameterized statements.
2. If a message ID already exists locally, the entry is idempotently refreshed without creating duplicates or altering display ordering.
3. Querying conversation streams via `get_messages(contact_id)` filters by `(sender_id = :cid AND recipient_id = :me) OR (sender_id = :me AND recipient_id = :cid)` ordered strictly by `timestamp ASC`.

---

## Installation & Running

### 1. Prerequisites
- **Python 3.10+** (tested on Python 3.10 through 3.14 on Windows, macOS, and Linux)
- `Tkinter` (bundled with official Python installers on Windows and macOS)

### 2. Setup Virtual Environment

```bash
# Clone repository
git clone https://github.com/your-username/MessagingAppFrontend.git
cd MessagingAppFrontend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Command Line Interface

Show available CLI options:
```bash
python -m src.messaging_app.main --help
```

Output:
```
NexusChat - Modern Desktop Messaging Application

Usage: python -m src.messaging_app.main [options]

Options:
  -h, --help  Show this help message and exit.

Configuration is loaded from environment variables or .env file.
Supported environment variables:
  SERVER_IP            Server IP address (default: 127.0.0.1)
  SERVER_PORT          Server TCP port (default: 9000)
  CLIENT_USER_ID       Current user unique ID
  CLIENT_USERNAME      Current user handle
  CLIENT_DISPLAY_NAME  Current user display name
  LOCAL_DB_PATH        Path to SQLite cache database
```

### 4. Running the Application

Run directly using the production TCP service:
```bash
python -m src.messaging_app.main
```

Or configure custom connection parameters via environment variables:
```bash
# Example with custom server and user identity (PowerShell)
$env:SERVER_IP="192.168.1.50"
$env:SERVER_PORT="9000"
$env:CLIENT_USERNAME="alice"
$env:CLIENT_DISPLAY_NAME="Alice Smith"
python -m src.messaging_app.main
```

---

## Testing

The project is backed by an automated test suite containing **86 unit and integration tests** with 100% pass rate.

Run the test suite with `pytest`:

```bash
pytest -v
```

### Test Suite Structure

| Test File | Focus Area |
|---|---|
| `tests/test_config.py` | Environment variable parsing, type coercions, fallback defaults, and immutability |
| `tests/test_cache.py` | SQLite schema creation, CRUD operations, indexing, and sync deduplication |
| `tests/test_protocol_frames.py` | NDJSON packet encoding, stream decoding, and payload builders (`receiver_id`) |
| `tests/test_tcp_client.py` | TCP socket lifecycle, background threads, auto-reconnect backoff, and error recovery |
| `tests/test_tcp_service.py` | `TcpMessagingService` integration with cache, network queries, and protocol compliance |
| `tests/test_ui_tcp_integration.py` | Connection status indicators, live presence updates, and modal verifying states |
| `tests/test_main.py` | CLI flags (`--help`, `-h`), component lifecycle orchestration, and `finally:` teardown |
| `tests/test_sidebar.py` | Contact filtering, search, selection callbacks, and hover states |
| `tests/test_chat_area.py` | Message stream rendering, empty states, and composer key bindings |
| `tests/test_message_bubble.py` | Speech bubble formatting, avatar initials, and timestamps |
| `tests/test_add_user_modal.py` | Modal validation, keyboard shortcuts (<kbd>Return</kbd>, <kbd>Escape</kbd>), and cancel |
| `tests/test_app_integration.py` | End-to-end coordinator lifecycle and cross-component integration |

---

## Design System Tokens

Located in [`src/messaging_app/ui/theme.py`](file:///D:/Sync/Projects/MessagingAppFrontend/src/messaging_app/ui/theme.py):

| Token | Light Mode | Dark Mode | Description |
|---|---|---|---|
| `BG_ROOT` | `#F8FAFC` | `#111318` | Window background surface |
| `BG_SIDEBAR` | `#EDF2F7` | `#181B22` | Navigation sidebar background |
| `BG_SURFACE` | `#FFFFFF` | `#222631` | Cards, modals, and conversation canvas |
| `BG_HOVER` | `#E2E8F0` | `#2B303E` | Hover interaction state |
| `PRIMARY` | `#4F46E5` | `#6366F1` | Brand Indigo accent |
| `PRIMARY_HOVER`| `#4338CA` | `#4F46E5` | Active / button hover state |
| `BUBBLE_OUT` | `#4F46E5` | `#4F46E5` | Outgoing message bubble surface |
| `BUBBLE_IN` | `#FFFFFF` | `#222631` | Incoming message bubble surface |
| `TEXT_PRIMARY` | `#0F172A` | `#F1F5F9` | High-contrast body text |
| `TEXT_SECONDARY`| `#64748B` | `#94A3B8` | Subtle metadata, timestamps, and usernames |
| `STATUS_ONLINE`| `#10B981` | `#10B981` | Emerald online presence dot |
| `STATUS_OFFLINE`| `#94A3B8` | `#64748B` | Subtle offline presence dot |

---

## License

This project is licensed under the MIT License — see the LICENSE file for details.
