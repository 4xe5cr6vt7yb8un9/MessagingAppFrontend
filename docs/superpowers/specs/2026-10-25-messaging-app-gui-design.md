# Messaging App Frontend GUI — Design Specification

**Date:** 2026-10-25  
**Status:** Approved  
**Framework:** CustomTkinter + Pillow  
**Icons:** Lucide Icons (via `better-icons`)  
**Design Paradigm:** Adaptive Dual-Theme (Dark Slate & Indigo default), Modular Event-Driven Architecture  

---

## 1. Overview & Objectives

The goal of this project is to construct a modern, responsive, and visually polished desktop messaging application frontend in Python. The application provides an interface for:
1. Sending messages with instant visual feedback and keyboard shortcuts.
2. Receiving messages with realistic simulated auto-replies via an in-memory dummy service.
3. Adding new user contacts with real-time sidebar updates.
4. Filtering/searching contacts dynamically.
5. Seamlessly swapping dummy functions for real networking (WebSockets, REST APIs, or sockets) in the future without modifying any UI code.

---

## 2. Architecture & File Layout

Following `python-patterns` and `coding-standards`, the application is structured with strict separation of concerns into models, services, UI components, and assets:

```
MessagingAppFrontend/
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-10-25-messaging-app-gui-design.md
├── src/
│   └── messaging_app/
│       ├── __init__.py
│       ├── main.py                   # Application entry point
│       ├── models/
│       │   ├── __init__.py
│       │   ├── user.py               # User entity dataclass
│       │   └── message.py            # Message entity dataclass
│       ├── services/
│       │   ├── __init__.py
│       │   ├── protocol.py           # MessagingServiceProtocol definition
│       │   └── dummy_service.py      # In-memory mock service with simulated replies
│       └── ui/
│           ├── __init__.py
│           ├── app.py                # Root CTk window & layout manager
│           ├── theme.py              # Color palette, radii, fonts & tokens
│           ├── icons.py              # Icon loader & SVG-to-CTkImage helper
│           ├── assets/
│           │   └── icons/            # Downloaded Lucide SVGs / raster assets
│           └── components/
│               ├── __init__.py
│               ├── sidebar.py        # Contacts list, search bar, add user trigger
│               ├── chat_area.py      # Conversation header, bubble stream, input composer
│               ├── message_bubble.py # Custom speech bubble widget
│               └── add_user_modal.py # CTkToplevel modal dialog to add new contacts
├── requirements.txt                  # customtkinter, pillow
└── README.md
```

---

## 3. Data Models (`src/messaging_app/models/`)

Data models are clean, immutable dataclasses (`frozen=True`) to prevent accidental state mutation:

### 3.1 `User` (`user.py`)
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class User:
    id: str
    username: str
    display_name: str
    avatar_initials: str
    is_online: bool = False
```

### 3.2 `Message` (`message.py`)
```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass(frozen=True)
class Message:
    id: str
    sender_id: str
    recipient_id: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    is_outgoing: bool = False
```

---

## 4. Service Abstraction (`src/messaging_app/services/`)

### 4.1 `MessagingServiceProtocol` (`protocol.py`)
The UI interacts exclusively through a Python `Protocol`, guaranteeing zero coupling to internal storage or networking mechanisms:

```python
from typing import Callable, Protocol
from messaging_app.models.user import User
from messaging_app.models.message import Message

class MessagingServiceProtocol(Protocol):
    def get_current_user(self) -> User: ...
    def get_contacts(self) -> list[User]: ...
    def get_messages(self, contact_id: str) -> list[Message]: ...
    def send_message(self, recipient_id: str, content: str) -> Message: ...
    def add_contact(self, username: str, display_name: str) -> User: ...
    def subscribe_message_received(self, callback: Callable[[Message], None]) -> None: ...
    def subscribe_contact_added(self, callback: Callable[[User], None]) -> None: ...
```

### 4.2 `DummyMessagingService` (`dummy_service.py`)
An interactive in-memory implementation:
* **Pre-seeded data:**
  * Current user: "You" (`@me`).
  * Contacts: Alice Smith (`@alice`, online), Bob Martinez (`@bob`, offline), Charlie Kim (`@charlie`, online).
  * Sample conversations with preloaded message histories.
* **`send_message(recipient_id, content)`:**
  * Stores message in local state and returns it.
  * Dispatches an asynchronous timer (`threading.Timer(1.2, ...)` or `root.after`) to trigger a contextual simulated reply from the contact.
* **`add_contact(username, display_name)`:**
  * Validates non-empty input and duplicate check.
  * Creates `User` with auto-computed avatar initials.
  * Invokes `subscribe_contact_added` subscribers so the UI refreshes immediately.

---

## 5. UI Layout & Component Architecture (`src/messaging_app/ui/`)

### 5.1 Root Window (`app.py`)
* Root class inherits from `customtkinter.CTk`.
* Default window geometry: `1024×720px` (min: `880×580px`).
* Two-column grid layout:
  * Column 0 (weight 0): `Sidebar` frame, fixed width 300px.
  * Column 1 (weight 1): `ChatArea` frame, dynamically resizing.

### 5.2 Sidebar (`components/sidebar.py`)
* **Header:** Current user profile badge + theme toggle button (Dark/Light).
* **Search Entry:** Real-time filter entry with magnifying glass icon.
* **Add Contact Button:** Full-width primary button with `lucide:user-plus` icon.
* **Scrollable Contact List:** `CTkScrollableFrame` rendering contact cards with:
  * Avatar badge with initials and status dot (green = online, gray = offline).
  * Display name in bold, `@username` in secondary color.
  * Last message snippet.
  * Selected state highlight and hover feedback.

### 5.3 Chat Area (`components/chat_area.py`)
* **Header Bar:** Active contact avatar, full name, and online/offline pill status.
* **Message Stream:** `CTkScrollableFrame` hosting `MessageBubble` widgets. Automatically scrolls to bottom on new messages.
* **Empty State:** Graphic placeholder card when no conversation is active or message history is empty.
* **Input Composer:**
  * Multiline/single-line wrap text entry with placeholder.
  * Send button with paper-plane icon (`lucide:send`).
  * Shortcuts: <kbd>Enter</kbd> to send, <kbd>Shift</kbd>+<kbd>Enter</kbd> for newline.

### 5.4 Message Bubble (`components/message_bubble.py`)
* **Outgoing:** Right-aligned, Indigo accent surface (`#4F46E5`), white text, timestamp in lower right.
* **Incoming:** Left-aligned, dark slate card surface (`#222631`), contact initials badge, timestamp in lower right.
* Formatted timestamps (`%I:%M %p`) using tabular numeral spacing.

### 5.5 Add User Modal (`components/add_user_modal.py`)
* `CTkToplevel` modal dialog centered over parent window.
* Input fields for `@username` and `Display Name`.
* Inline error label for validation feedback.
* Action buttons: "Add Contact" (primary) and "Cancel" (ghost/secondary).

---

## 6. Design System & Polish Tokens (`theme.py`)

Applying `make-interfaces-feel-better` and `design`:

### 6.1 Color Palette
CustomTkinter `(light_mode, dark_mode)` token definitions:
* `BG_ROOT`: `("#F8FAFC", "#111318")`
* `BG_SIDEBAR`: `("#EDF2F7", "#181B22")`
* `BG_SURFACE`: `("#FFFFFF", "#222631")`
* `BG_HOVER`: `("#E2E8F0", "#2B303E")`
* `PRIMARY`: `("#4F46E5", "#6366F1")`
* `PRIMARY_HOVER`: `("#4338CA", "#4F46E5")`
* `BUBBLE_OUT`: `("#4F46E5", "#4F46E5")`
* `BUBBLE_IN`: `("#FFFFFF", "#222631")`
* `TEXT_PRIMARY`: `("#0F172A", "#F1F5F9")`
* `TEXT_SECONDARY`: `("#64748B", "#94A3B8")`
* `BORDER`: `("#CBD5E1", "#2E3442")`
* `STATUS_ONLINE`: `("#10B981", "#10B981")`

### 6.2 Micro-Interactions & Dimensions
* **Concentric Radii:** Outer cards `corner_radius=12`, inner buttons/chips `corner_radius=8`.
* **Hit Areas:** All clickable buttons maintain at least `40px` (ideally `44px`) height.
* **Optical Alignment:** Centered icons with calibrated internal padding.
* **Typography:** `Segoe UI` on Windows, falling back to clean sans-serif.

---

## 7. Icons (`better-icons`)

Retrieved via `better-icons get <id>` and cached in `src/messaging_app/ui/assets/icons/`:
* `lucide:send` — Send message action.
* `lucide:user-plus` — Add contact action.
* `lucide:search` — Search bar icon.
* `lucide:sun` / `lucide:moon` — Theme toggle icons.
* `lucide:message-square` — Logo and empty chat state.
* `lucide:check-check` — Outgoing message delivery receipts.

---

## 8. Verification & Testing Strategy

1. **Unit Tests (`tests/test_services.py`):**
   * Verify `DummyMessagingService` creates contacts, updates state, and handles message appending.
   * Verify contact search filtering.
2. **UI Integration Verification:**
   * Launch application: verify dark mode rendering, responsive resizing, and icon crispness.
   * Send outgoing message: verify immediate bubble render and autoscroll.
   * Receive incoming message: verify simulated reply appears after delay.
   * Add new contact: verify modal validation and real-time sidebar card insertion.
   * Theme toggle: verify smooth switch between Dark and Light mode.
