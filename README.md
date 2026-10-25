# NexusChat — Modern Desktop Messaging Application

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/GUI-CustomTkinter-indigo.svg)](https://customtkinter.tomschimansky.com/)
[![Tests](https://img.shields.io/badge/Tests-45%20Passing-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-gray.svg)]()

**NexusChat** is a responsive, modern desktop messaging application built in Python using **CustomTkinter** and **Pillow**. Designed with clean separation of concerns and an adaptive dual-theme design system, NexusChat features an asynchronous in-memory simulation engine that can be swapped for real networking backends (WebSockets, REST APIs, or TCP sockets) without modifying a single line of UI code.

---

## Features

- **Responsive Two-Column Layout**: Fixed-width sidebar with scrollable contact cards and a fluid, auto-resizing chat canvas.
- **Message Stream & Speech Bubbles**:
  - Right-aligned outgoing bubbles with accent coloring and delivery receipt status.
  - Left-aligned incoming bubbles with contact initials badge and distinct surface background.
  - Formatted timestamps (`%I:%M %p`) and automatic scroll-to-bottom on new messages.
  - Elegant empty state placeholders when no contact is selected.
- **Simulated Asynchronous Auto-Replies**:
  - Realistic multi-threaded response simulation (`DummyMessagingService`) with configurable reply delays.
  - Thread-safe UI updates dispatched via the Tkinter main event loop.
- **Real-Time Contact Search**:
  - Dynamic filtering of contacts by display name or `@username`.
  - Instant visual feedback with empty search fallback indicators.
- **Contact Management Dialog (`AddUserModal`)**:
  - Centered modal dialog with input validation, duplicate username detection, and whitespace trimming.
  - Automatic avatar initials computation.
  - Instant synchronization with the sidebar via pub/sub callbacks.
- **Adaptive Dual Theme**:
  - One-click toggle between **Dark Slate & Indigo** and **Light Clean** palettes.
  - High-DPI crisp vector icons (Lucide icons rendered via Pillow and CustomTkinter).
- **Keyboard Shortcuts**:
  - <kbd>Enter</kbd> to send a message.
  - <kbd>Shift</kbd> + <kbd>Enter</kbd> for a multi-line newline.
  - <kbd>Enter</kbd> to submit in modal dialogs; <kbd>Escape</kbd> to cancel and dismiss.

---

## Architecture & Directory Layout

NexusChat strictly adheres to the **Model-View-Service** architectural pattern. The user interface depends solely on the abstract `MessagingServiceProtocol`, decoupling business logic and transport protocols from graphical presentation.

```
MessagingAppFrontend/
├── docs/
│   └── superpowers/
│       ├── specs/2026-10-25-messaging-app-gui-design.md
│       └── plans/2026-10-25-messaging-app-gui-plan.md
├── src/
│   └── messaging_app/
│       ├── __init__.py
│       ├── main.py                     # Main application entry point
│       ├── models/                     # Immutable frozen data entities
│       │   ├── __init__.py
│       │   ├── user.py                 # User dataclass (id, username, display_name, ...)
│       │   └── message.py              # Message dataclass (id, sender, recipient, timestamp, ...)
│       ├── services/                   # Business logic and transport layer
│       │   ├── __init__.py
│       │   ├── protocol.py             # MessagingServiceProtocol definition
│       │   └── dummy_service.py        # In-memory service with simulated auto-replies
│       └── ui/                         # Presentation layer (CustomTkinter)
│           ├── __init__.py
│           ├── app.py                  # Root MessagingApp window & coordinator
│           ├── theme.py                # Design tokens, color palettes & radii
│           ├── icons.py                # Lucide SVG rasterizer and CTkImage loader
│           ├── assets/
│           │   └── icons/              # Embedded vector SVG icons
│           └── components/             # Reusable UI widgets
│               ├── __init__.py
│               ├── sidebar.py          # Header, search bar & contact cards
│               ├── chat_area.py        # Chat header, message stream & composer
│               ├── message_bubble.py   # Speech bubble widget with initials & timestamps
│               └── add_user_modal.py   # Modal dialog for adding contacts
├── tests/                              # Comprehensive unit and integration test suite
│   ├── conftest.py                     # Root test fixtures and path configuration
│   ├── test_add_user_modal.py
│   ├── test_app_integration.py
│   ├── test_chat_area.py
│   ├── test_environment.py
│   ├── test_message_bubble.py
│   ├── test_models.py
│   ├── test_services.py
│   ├── test_sidebar.py
│   └── test_theme_and_icons.py
├── requirements.txt                    # Python dependencies
└── README.md                           # Documentation
```

---

## Installation & Running

### 1. Prerequisites
- **Python 3.10+** (tested on Python 3.10, 3.11, 3.12, 3.13, and 3.14 on Windows, macOS, and Linux)
- `Tkinter` (included by default with standard Windows and macOS Python installers)

### 2. Clone and Setup Environment

```bash
# Clone the repository
git clone https://github.com/your-username/MessagingAppFrontend.git
cd MessagingAppFrontend

# Create and activate a virtual environment
python -m venv venv

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# On macOS/Linux:
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Launch Application

Run the application as a Python module:

```bash
python -m src.messaging_app.main
```

Or run directly:

```bash
python src/messaging_app/main.py
```

To see available command-line flags:

```bash
python -m src.messaging_app.main --help
```

---

## Running the Test Suite

The project includes a 45-test automated test suite covering models, services, UI components, modal workflows, and end-to-end integration flows.

Run all tests with `pytest`:

```bash
pytest -v
```

Output:
```
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.1.1
collected 45 items

tests/test_add_user_modal.py ......                                      [ 13%]
tests/test_app_integration.py .......                                    [ 28%]
tests/test_chat_area.py ......                                           [ 42%]
tests/test_environment.py .                                              [ 44%]
tests/test_message_bubble.py ....                                        [ 53%]
tests/test_models.py .....                                               [ 64%]
tests/test_services.py .......                                           [ 80%]
tests/test_sidebar.py .....                                              [ 91%]
tests/test_theme_and_icons.py ....                                       [100%]

============================= 45 passed in 9.98s ==============================
```

---

## User Experience & Interactions

| Feature | How to Trigger / Interact |
|---|---|
| **Select a Contact** | Click any contact card in the left sidebar to open the conversation history. |
| **Send Message** | Type in the bottom text entry and press <kbd>Enter</kbd> (or click the Send button). |
| **Multi-line Text** | Press <kbd>Shift</kbd> + <kbd>Enter</kbd> in the composer. |
| **Simulated Replies** | Sending any message to an online contact triggers an asynchronous simulated reply after ~1.2 seconds. |
| **Add New Contact** | Click **"Add Contact"** in the sidebar. Fill in `@username` and `Display Name`, then press <kbd>Enter</kbd>. |
| **Filter Contacts** | Type in the search box at the top of the sidebar. The list updates instantly. |
| **Theme Toggle** | Click the Moon/Sun icon in the sidebar header to switch between Dark and Light mode. |
| **Dismiss Modal** | Press <kbd>Escape</kbd> or click **"Cancel"** to close the Add Contact dialog. |

---

## Decoupled Service Architecture: Integrating Real Networking

The UI components never import `DummyMessagingService` directly. They interact with `MessagingServiceProtocol`, defined in [`src/messaging_app/services/protocol.py`](file:///D:/Sync/Projects/MessagingAppFrontend/src/messaging_app/services/protocol.py):

```python
from typing import Callable, Protocol
from messaging_app.models.message import Message
from messaging_app.models.user import User

class MessagingServiceProtocol(Protocol):
    def get_current_user(self) -> User: ...
    def get_contacts(self) -> list[User]: ...
    def get_messages(self, contact_id: str) -> list[Message]: ...
    def send_message(self, recipient_id: str, content: str) -> Message: ...
    def add_contact(self, username: str, display_name: str) -> User: ...
    def subscribe_message_received(self, callback: Callable[[Message], None]) -> None: ...
    def subscribe_contact_added(self, callback: Callable[[User], None]) -> None: ...
```

### Swapping for Real Networking (e.g., WebSockets / REST)

To connect NexusChat to a live backend (such as a WebSocket gateway, Matrix, or REST API), create a new class implementing `MessagingServiceProtocol`:

```python
# src/messaging_app/services/websocket_service.py

import json
import threading
from typing import Callable
import websockets
from messaging_app.models.message import Message
from messaging_app.models.user import User
from messaging_app.services.protocol import MessagingServiceProtocol

class WebSocketMessagingService(MessagingServiceProtocol):
    def __init__(self, server_url: str, auth_token: str) -> None:
        self.server_url = server_url
        self.auth_token = auth_token
        self._message_callbacks: list[Callable[[Message], None]] = []
        self._contact_callbacks: list[Callable[[User], None]] = []
        # Connect to background socket thread...

    def get_current_user(self) -> User:
        return self._cached_current_user

    def get_contacts(self) -> list[User]:
        return list(self._cached_contacts.values())

    def get_messages(self, contact_id: str) -> list[Message]:
        return list(self._cached_messages.get(contact_id, []))

    def send_message(self, recipient_id: str, content: str) -> Message:
        # Transmit payload over WebSocket connection
        msg = Message(
            id=generate_uuid(),
            sender_id=self.get_current_user().id,
            recipient_id=recipient_id,
            content=content,
            is_outgoing=True,
        )
        self._ws_send({"type": "chat.message", "data": msg})
        return msg

    def add_contact(self, username: str, display_name: str) -> User:
        # Send contact invite request to server
        user = User(id=generate_uuid(), username=username, display_name=display_name, avatar_initials="...")
        self._ws_send({"type": "contact.add", "data": user})
        return user

    def subscribe_message_received(self, callback: Callable[[Message], None]) -> None:
        self._message_callbacks.append(callback)

    def subscribe_contact_added(self, callback: Callable[[User], None]) -> None:
        self._contact_callbacks.append(callback)
```

Then in [`src/messaging_app/main.py`](file:///D:/Sync/Projects/MessagingAppFrontend/src/messaging_app/main.py), simply inject your live service into `MessagingApp`:

```python
from messaging_app.services.websocket_service import WebSocketMessagingService
from messaging_app.ui.app import MessagingApp

def main() -> None:
    service = WebSocketMessagingService(server_url="wss://chat.example.com/ws", auth_token="...")
    app = MessagingApp(service=service)
    app.mainloop()
```

The entire UI layer (`MessagingApp`, `Sidebar`, `ChatArea`, and `AddUserModal`) will function without any modifications.

---

## Design System Tokens

NexusChat includes a centralized design system located in [`src/messaging_app/ui/theme.py`](file:///D:/Sync/Projects/MessagingAppFrontend/src/messaging_app/ui/theme.py):

| Token | Light Mode | Dark Mode | Description |
|---|---|---|---|
| `BG_ROOT` | `#F8FAFC` | `#111318` | Window background surface |
| `BG_SIDEBAR` | `#EDF2F7` | `#181B22` | Navigation sidebar background |
| `BG_SURFACE` | `#FFFFFF` | `#222631` | Cards and conversation canvas |
| `BG_HOVER` | `#E2E8F0` | `#2B303E` | Hover feedback state |
| `PRIMARY` | `#4F46E5` | `#6366F1` | Brand Indigo accent |
| `PRIMARY_HOVER`| `#4338CA` | `#4F46E5` | Active / hover button state |
| `BUBBLE_OUT` | `#4F46E5` | `#4F46E5` | Outgoing message bubble surface |
| `BUBBLE_IN` | `#FFFFFF` | `#222631` | Incoming message bubble surface |
| `TEXT_PRIMARY` | `#0F172A` | `#F1F5F9` | High-contrast body typography |
| `TEXT_SECONDARY`| `#64748B` | `#94A3B8` | Subtle metadata and timestamps |
| `STATUS_ONLINE`| `#10B981` | `#10B981` | Emerald online indicator dot |

---

## Contributing & Development

1. Follow PEP 8 guidelines and type annotation standards (`typing.Optional`, `typing.Callable`, `Protocol`).
2. Keep data models immutable (`@dataclass(frozen=True)`).
3. Ensure all new components export via `__init__.py` and have unit test coverage.
4. Verify tests pass prior to submitting changes:
   ```bash
   pytest -v
   ```
