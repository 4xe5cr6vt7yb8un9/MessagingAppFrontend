# Python Messaging App Frontend GUI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a modern, modular, responsive desktop messaging application frontend GUI in Python using CustomTkinter, Pillow, and Lucide icons via `better-icons`, featuring message sending/receiving with interactive simulated replies, contact management, search filtering, and an adaptive dark/light theme.

**Architecture:** Modular event-driven architecture strictly separating clean immutable data models (`models/`), a decoupled service layer (`services/` implementing `MessagingServiceProtocol`), and reusable UI components (`ui/components/`) built on CustomTkinter. Future transition to real backend services requires zero UI code modifications.

**Tech Stack:** Python 3.14+, `customtkinter`, `pillow`, `pytest`, `better-icons` CLI.

**Spec:** [`docs/superpowers/specs/2026-10-25-messaging-app-gui-design.md`](file:///d:/Sync/Projects/MessagingAppFrontend/docs/superpowers/specs/2026-10-25-messaging-app-gui-design.md)

## Global Constraints
- Naming & Style: Follow PEP 8 and `python-patterns` (descriptive names, type annotations everywhere, explicit exception handling).
- Immutability: Data models (`User`, `Message`) must be frozen dataclasses.
- Code Standards: Single responsibility per component; no monolithic classes; max 150-200 lines per file.
- Polish Guidelines (`make-interfaces-feel-better`): Concentric radii (`corner_radius=12` on outer cards, `8` on inner elements), minimum 40px to 44px hit areas on interactive controls, optical icon centering, tabular numerals for timestamps.
- Zero Hard Coupling: GUI widgets communicate only through `MessagingServiceProtocol`.

---

## Tasks

### Task 1: Environment & Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `src/messaging_app/__init__.py`
- Create: `tests/__init__.py`
- Test: `tests/test_environment.py`

**Interfaces:**
- Consumes: Python standard library, pip packages.
- Produces: Installed dependencies (`customtkinter`, `pillow`, `pytest`) and base package layout.

- [ ] **Step 1: Write requirements.txt**

```text
customtkinter>=6.0.0
pillow>=10.0.0
pytest>=7.4.0
```

- [ ] **Step 2: Install dependencies**

Run: `python -m pip install -r requirements.txt`  
Expected: Successfully installed customtkinter, pillow, pytest.

- [ ] **Step 3: Create package structure and write test_environment.py**

Create `src/messaging_app/__init__.py` and `tests/__init__.py`.  
Write `tests/test_environment.py`:
```python
import customtkinter
import PIL
import pytest

def test_libraries_importable():
    assert customtkinter.__name__ == "customtkinter"
    assert PIL.__name__ == "PIL"
```

- [ ] **Step 4: Run test to verify environment**

Run: `pytest tests/test_environment.py -v`  
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add requirements.txt src/ tests/
git commit -m "chore: setup project structure and python dependencies"
```

---

### Task 2: Data Models (`User`, `Message`)

**Files:**
- Create: `src/messaging_app/models/__init__.py`
- Create: `src/messaging_app/models/user.py`
- Create: `src/messaging_app/models/message.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: Standard library `dataclasses`, `datetime`.
- Produces:
  - `User(id: str, username: str, display_name: str, avatar_initials: str, is_online: bool = False)`
  - `Message(id: str, sender_id: str, recipient_id: str, content: str, timestamp: datetime, is_outgoing: bool = False)`

- [ ] **Step 1: Write the failing tests**

Write `tests/test_models.py`:
```python
from datetime import datetime
import pytest
from messaging_app.models.user import User
from messaging_app.models.message import Message

def test_user_creation_and_immutability():
    user = User(
        id="u1",
        username="alice",
        display_name="Alice Smith",
        avatar_initials="AS",
        is_online=True
    )
    assert user.id == "u1"
    assert user.username == "alice"
    assert user.display_name == "Alice Smith"
    assert user.avatar_initials == "AS"
    assert user.is_online is True

    with pytest.raises(Exception):
        user.display_name = "Alice Doe"

def test_message_creation_and_defaults():
    msg = Message(
        id="m1",
        sender_id="u1",
        recipient_id="u2",
        content="Hello world!",
        is_outgoing=True
    )
    assert msg.id == "m1"
    assert msg.content == "Hello world!"
    assert msg.is_outgoing is True
    assert isinstance(msg.timestamp, datetime)

    with pytest.raises(Exception):
        msg.content = "Mutated"
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_models.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'messaging_app.models'`.

- [ ] **Step 3: Implement data models**

Create `src/messaging_app/models/__init__.py`:
```python
from messaging_app.models.user import User
from messaging_app.models.message import Message

__all__ = ["User", "Message"]
```

Create `src/messaging_app/models/user.py`:
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

Create `src/messaging_app/models/message.py`:
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

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_models.py -v`  
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add src/messaging_app/models/ tests/test_models.py
git commit -m "feat(models): add User and Message frozen dataclasses"
```

---

### Task 3: Service Protocol & Interactive Dummy Messaging Service

**Files:**
- Create: `src/messaging_app/services/__init__.py`
- Create: `src/messaging_app/services/protocol.py`
- Create: `src/messaging_app/services/dummy_service.py`
- Test: `tests/test_services.py`

**Interfaces:**
- Consumes: `messaging_app.models.user.User`, `messaging_app.models.message.Message`.
- Produces:
  - `MessagingServiceProtocol` (Protocol)
  - `DummyMessagingService` implementing the protocol with:
    - `get_current_user() -> User`
    - `get_contacts() -> list[User]`
    - `get_messages(contact_id: str) -> list[Message]`
    - `send_message(recipient_id: str, content: str) -> Message`
    - `add_contact(username: str, display_name: str) -> User`
    - `subscribe_message_received(callback: Callable[[Message], None]) -> None`
    - `subscribe_contact_added(callback: Callable[[User], None]) -> None`

- [ ] **Step 1: Write the failing tests**

Write `tests/test_services.py`:
```python
import time
import pytest
from messaging_app.services.dummy_service import DummyMessagingService
from messaging_app.services.protocol import MessagingServiceProtocol
from messaging_app.models.message import Message
from messaging_app.models.user import User

def test_dummy_service_implements_protocol():
    service = DummyMessagingService()
    assert isinstance(service, MessagingServiceProtocol)

def test_initial_contacts_and_current_user():
    service = DummyMessagingService()
    current_user = service.get_current_user()
    assert current_user.username == "me"

    contacts = service.get_contacts()
    assert len(contacts) >= 3
    alice = next((c for c in contacts if c.username == "alice"), None)
    assert alice is not None
    assert alice.display_name == "Alice Smith"

def test_send_message_and_simulation():
    service = DummyMessagingService(simulation_delay=0.05)
    received_replies: list[Message] = []
    service.subscribe_message_received(lambda msg: received_replies.append(msg))

    msg = service.send_message(recipient_id="alice", content="Hey Alice!")
    assert msg.content == "Hey Alice!"
    assert msg.is_outgoing is True

    # Check that outgoing message is stored in conversation
    history = service.get_messages("alice")
    assert any(m.id == msg.id for m in history)

    # Wait for simulated reply
    time.sleep(0.1)
    assert len(received_replies) == 1
    assert received_replies[0].sender_id == "alice"
    assert received_replies[0].is_outgoing is False

def test_add_contact_success_and_validation():
    service = DummyMessagingService()
    added_users: list[User] = []
    service.subscribe_contact_added(lambda u: added_users.append(u))

    new_user = service.add_contact(username="david", display_name="David Miller")
    assert new_user.username == "david"
    assert new_user.avatar_initials == "DM"
    assert len(added_users) == 1

    # Check duplicate prevention
    with pytest.raises(ValueError, match="already exists"):
        service.add_contact(username="david", display_name="David Clone")

    # Check empty username prevention
    with pytest.raises(ValueError, match="cannot be empty"):
        service.add_contact(username="   ", display_name="Invalid")
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_services.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'messaging_app.services'`.

- [ ] **Step 3: Implement protocol and DummyMessagingService**

Create `src/messaging_app/services/protocol.py`:
```python
from typing import Callable, Protocol, runtime_checkable
from messaging_app.models.user import User
from messaging_app.models.message import Message

@runtime_checkable
class MessagingServiceProtocol(Protocol):
    def get_current_user(self) -> User: ...
    def get_contacts(self) -> list[User]: ...
    def get_messages(self, contact_id: str) -> list[Message]: ...
    def send_message(self, recipient_id: str, content: str) -> Message: ...
    def add_contact(self, username: str, display_name: str) -> User: ...
    def subscribe_message_received(self, callback: Callable[[Message], None]) -> None: ...
    def subscribe_contact_added(self, callback: Callable[[User], None]) -> None: ...
```

Create `src/messaging_app/services/dummy_service.py`:
```python
import random
import threading
import uuid
from datetime import datetime
from typing import Callable
from messaging_app.models.user import User
from messaging_app.models.message import Message

class DummyMessagingService:
    """In-memory interactive dummy messaging service with realistic simulation."""

    def __init__(self, simulation_delay: float = 1.2) -> None:
        self.simulation_delay = simulation_delay
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
            User("alice", "alice", "Alice Smith", "AS", is_online=True),
            User("bob", "bob", "Bob Martinez", "BM", is_online=False),
            User("charlie", "charlie", "Charlie Kim", "CK", is_online=True),
        ]

        self._messages: dict[str, list[Message]] = {
            "alice": [
                Message("m1", "alice", "me", "Hi there! How is the project going?", datetime.now(), is_outgoing=False),
                Message("m2", "me", "alice", "Making great progress on the frontend!", datetime.now(), is_outgoing=True),
            ],
            "bob": [
                Message("m3", "bob", "me", "Catch you tomorrow!", datetime.now(), is_outgoing=False),
            ],
            "charlie": [
                Message("m4", "charlie", "me", "Hey, do you have that report?", datetime.now(), is_outgoing=False),
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
        return self._current_user

    def get_contacts(self) -> list[User]:
        return list(self._contacts)

    def get_messages(self, contact_id: str) -> list[Message]:
        return list(self._messages.get(contact_id, []))

    def send_message(self, recipient_id: str, content: str) -> Message:
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

        if recipient_id not in self._messages:
            self._messages[recipient_id] = []
        self._messages[recipient_id].append(msg)

        # Trigger background simulated reply
        if self.simulation_delay > 0:
            timer = threading.Timer(self.simulation_delay, self._dispatch_simulated_reply, args=(recipient_id,))
            timer.daemon = True
            timer.start()

        return msg

    def _dispatch_simulated_reply(self, contact_id: str) -> None:
        reply_text = random.choice(self._simulation_responses)
        reply_msg = Message(
            id=str(uuid.uuid4())[:8],
            sender_id=contact_id,
            recipient_id=self._current_user.id,
            content=reply_text,
            timestamp=datetime.now(),
            is_outgoing=False,
        )

        if contact_id not in self._messages:
            self._messages[contact_id] = []
        self._messages[contact_id].append(reply_msg)

        for callback in self._message_callbacks:
            callback(reply_msg)

    def add_contact(self, username: str, display_name: str) -> User:
        clean_user = username.strip().lstrip("@")
        clean_name = display_name.strip()

        if not clean_user:
            raise ValueError("Username cannot be empty.")
        if not clean_name:
            clean_name = clean_user.capitalize()

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

        for callback in self._contact_callbacks:
            callback(new_user)

        return new_user

    def subscribe_message_received(self, callback: Callable[[Message], None]) -> None:
        self._message_callbacks.append(callback)

    def subscribe_contact_added(self, callback: Callable[[User], None]) -> None:
        self._contact_callbacks.append(callback)
```

Create `src/messaging_app/services/__init__.py`:
```python
from messaging_app.services.protocol import MessagingServiceProtocol
from messaging_app.services.dummy_service import DummyMessagingService

__all__ = ["MessagingServiceProtocol", "DummyMessagingService"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_services.py -v`  
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add src/messaging_app/services/ tests/test_services.py
git commit -m "feat(services): implement MessagingServiceProtocol and DummyMessagingService"
```

---

### Task 4: Theme Tokens & Icon System via `better-icons`

**Files:**
- Create: `src/messaging_app/ui/__init__.py`
- Create: `src/messaging_app/ui/theme.py`
- Create: `src/messaging_app/ui/assets/icons/`
- Create: `src/messaging_app/ui/icons.py`
- Test: `tests/test_theme_and_icons.py`

**Interfaces:**
- Consumes: `better-icons` CLI, `PIL.Image`, `customtkinter.CTkImage`.
- Produces:
  - `Theme` constants (`BG_ROOT`, `BG_SIDEBAR`, `BG_SURFACE`, `BG_HOVER`, `PRIMARY`, `PRIMARY_HOVER`, `BUBBLE_OUT`, `BUBBLE_IN`, `BORDER`, `TEXT_PRIMARY`, `TEXT_SECONDARY`, `STATUS_ONLINE`, `RADIUS_CARD`, `RADIUS_BUTTON`, `HIT_AREA_HEIGHT`).
  - `get_icon(name: str, size: tuple[int, int] = (20, 20))` -> `CTkImage`.

- [ ] **Step 1: Write the failing test**

Write `tests/test_theme_and_icons.py`:
```python
from messaging_app.ui.theme import Theme
from messaging_app.ui.icons import get_icon
import customtkinter

def test_theme_tokens():
    assert isinstance(Theme.PRIMARY, tuple)
    assert len(Theme.PRIMARY) == 2  # (light, dark)
    assert Theme.RADIUS_CARD == 12
    assert Theme.HIT_AREA_HEIGHT >= 40

def test_icon_retrieval():
    icon = get_icon("send", size=(20, 20))
    assert isinstance(icon, customtkinter.CTkImage)
    assert icon._size == (20, 20)
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_theme_and_icons.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'messaging_app.ui'`.

- [ ] **Step 3: Fetch Lucide icons using `better-icons` CLI and implement fallback generation**

Create icon directory: `src/messaging_app/ui/assets/icons/`.  
Run commands to download Lucide icons as SVGs:
```powershell
better-icons get lucide:send > src/messaging_app/ui/assets/icons/send.svg
better-icons get lucide:user-plus > src/messaging_app/ui/assets/icons/user-plus.svg
better-icons get lucide:search > src/messaging_app/ui/assets/icons/search.svg
better-icons get lucide:sun > src/messaging_app/ui/assets/icons/sun.svg
better-icons get lucide:moon > src/messaging_app/ui/assets/icons/moon.svg
better-icons get lucide:message-square > src/messaging_app/ui/assets/icons/message-square.svg
better-icons get lucide:check-check > src/messaging_app/ui/assets/icons/check-check.svg
```

Create `src/messaging_app/ui/theme.py`:
```python
class Theme:
    """UI Color tokens (Light, Dark), radii and spacing."""
    BG_ROOT = ("#F8FAFC", "#111318")
    BG_SIDEBAR = ("#EDF2F7", "#181B22")
    BG_SURFACE = ("#FFFFFF", "#222631")
    BG_HOVER = ("#E2E8F0", "#2B303E")
    BG_SELECTED = ("#E0E7FF", "#2E3447")

    PRIMARY = ("#4F46E5", "#6366F1")
    PRIMARY_HOVER = ("#4338CA", "#4F46E5")

    BUBBLE_OUT = ("#4F46E5", "#4F46E5")
    BUBBLE_IN = ("#FFFFFF", "#222631")

    TEXT_PRIMARY = ("#0F172A", "#F1F5F9")
    TEXT_SECONDARY = ("#64748B", "#94A3B8")
    TEXT_ON_PRIMARY = ("#FFFFFF", "#FFFFFF")

    BORDER = ("#CBD5E1", "#2E3442")
    STATUS_ONLINE = ("#10B981", "#10B981")
    STATUS_OFFLINE = ("#94A3B8", "#64748B")

    # Polish metrics (make-interfaces-feel-better)
    RADIUS_CARD = 12
    RADIUS_BUTTON = 8
    RADIUS_INPUT = 8
    HIT_AREA_HEIGHT = 42

    FONT_FAMILY = "Segoe UI"
```

Create `src/messaging_app/ui/icons.py`:
```python
from pathlib import Path
from PIL import Image, ImageDraw
import customtkinter

ASSETS_DIR = Path(__file__).parent / "assets" / "icons"
_ICON_CACHE: dict[tuple[str, tuple[int, int]], customtkinter.CTkImage] = {}

def _render_fallback_icon(name: str, size: tuple[int, int], color: str) -> Image.Image:
    """Generate high-DPI raster fallback icon when SVG parser is unavailable."""
    w, h = size[0] * 2, size[1] * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    m = 4
    if name == "send":
        draw.polygon([(m, m), (w - m, h // 2), (m, h - m), (m + 6, h // 2)], fill=color)
    elif name == "user-plus":
        draw.ellipse([(m, m), (w - m - 8, h - m - 8)], outline=color, width=3)
        draw.line([(w - 8, m + 4), (w - 8, m + 14)], fill=color, width=3)
        draw.line([(w - 13, m + 9), (w - 3, m + 9)], fill=color, width=3)
    elif name == "search":
        draw.ellipse([(m, m), (w - 12, h - 12)], outline=color, width=3)
        draw.line([(w - 14, h - 14), (w - m, h - m)], fill=color, width=3)
    elif name == "sun":
        draw.ellipse([(w // 4, h // 4), (3 * w // 4, 3 * h // 4)], fill=color)
    elif name == "moon":
        draw.ellipse([(m, m), (w - m, h - m)], fill=color)
        draw.ellipse([(m + 6, m - 2), (w - m + 6, h - m - 2)], fill=(0, 0, 0, 0))
    elif name == "message-square":
        draw.rounded_rectangle([(m, m), (w - m, h - m - 4)], radius=4, outline=color, width=3)
        draw.polygon([(m + 4, h - m - 4), (m + 10, h - m - 4), (m + 4, h - m + 4)], fill=color)
    else:
        draw.ellipse([(m, m), (w - m, h - m)], outline=color, width=2)
    return img

def get_icon(name: str, size: tuple[int, int] = (20, 20)) -> customtkinter.CTkImage:
    """Return a cached high-DPI CTkImage with automatic light/dark tinting."""
    key = (name, size)
    if key in _ICON_CACHE:
        return _ICON_CACHE[key]

    light_img = _render_fallback_icon(name, size, "#1E293B")
    dark_img = _render_fallback_icon(name, size, "#F8FAFC")
    ctk_image = customtkinter.CTkImage(light_image=light_img, dark_image=dark_img, size=size)
    _ICON_CACHE[key] = ctk_image
    return ctk_image
```

Create `src/messaging_app/ui/__init__.py`:
```python
from messaging_app.ui.theme import Theme
from messaging_app.ui.icons import get_icon

__all__ = ["Theme", "get_icon"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_theme_and_icons.py -v`  
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add src/messaging_app/ui/theme.py src/messaging_app/ui/icons.py src/messaging_app/ui/assets/ tests/test_theme_and_icons.py
git commit -m "feat(ui): add Theme color tokens and icon system"
```

---

### Task 5: Message Bubble Component

**Files:**
- Create: `src/messaging_app/ui/components/__init__.py`
- Create: `src/messaging_app/ui/components/message_bubble.py`
- Test: `tests/test_message_bubble.py`

**Interfaces:**
- Consumes: `messaging_app.models.message.Message`, `messaging_app.ui.theme.Theme`.
- Produces: `MessageBubble(parent, message: Message, contact_initials: str = "")` (CTkFrame subclass).

- [ ] **Step 1: Write the failing test**

Write `tests/test_message_bubble.py`:
```python
import customtkinter
from messaging_app.models.message import Message
from messaging_app.ui.components.message_bubble import MessageBubble

def test_message_bubble_creation():
    root = customtkinter.CTk()
    msg = Message("m1", "sender", "recipient", "Hello!", is_outgoing=True)
    bubble = MessageBubble(root, message=msg, contact_initials="AS")
    assert bubble.message.content == "Hello!"
    assert bubble.message.is_outgoing is True
    root.destroy()
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_message_bubble.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'messaging_app.ui.components'`.

- [ ] **Step 3: Implement MessageBubble**

Create `src/messaging_app/ui/components/__init__.py`:
```python
from messaging_app.ui.components.message_bubble import MessageBubble

__all__ = ["MessageBubble"]
```

Create `src/messaging_app/ui/components/message_bubble.py`:
```python
import customtkinter
from messaging_app.models.message import Message
from messaging_app.ui.theme import Theme

class MessageBubble(customtkinter.CTkFrame):
    """A stylized message bubble following concentric radius and optical alignment rules."""

    def __init__(
        self,
        master: any,
        message: Message,
        contact_initials: str = "",
        **kwargs
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.message = message

        is_out = message.is_outgoing
        time_str = message.timestamp.strftime("%I:%M %p")

        # Container frame
        bubble_frame = customtkinter.CTkFrame(
            self,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=Theme.BUBBLE_OUT if is_out else Theme.BUBBLE_IN,
            border_width=0 if is_out else 1,
            border_color=Theme.BORDER,
        )

        # Avatar for incoming message
        if not is_out:
            avatar = customtkinter.CTkLabel(
                self,
                text=contact_initials or "??",
                width=32,
                height=32,
                corner_radius=16,
                fg_color=Theme.PRIMARY,
                text_color="#FFFFFF",
                font=(Theme.FONT_FAMILY, 11, "bold"),
            )
            avatar.pack(side="left", anchor="e", padx=(0, 8), pady=(0, 4))
            bubble_frame.pack(side="left", anchor="w", padx=(0, 40))
        else:
            bubble_frame.pack(side="right", anchor="e", padx=(40, 0))

        # Message text label
        text_label = customtkinter.CTkLabel(
            bubble_frame,
            text=message.content,
            text_color=Theme.TEXT_ON_PRIMARY if is_out else Theme.TEXT_PRIMARY,
            font=(Theme.FONT_FAMILY, 13),
            wraplength=420,
            justify="left",
            anchor="w",
        )
        text_label.pack(padx=12, pady=(8, 2), anchor="w")

        # Timestamp row
        time_label = customtkinter.CTkLabel(
            bubble_frame,
            text=time_str,
            text_color="#CBD5E1" if is_out else Theme.TEXT_SECONDARY,
            font=(Theme.FONT_FAMILY, 10),
        )
        time_label.pack(padx=12, pady=(0, 6), anchor="e")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_message_bubble.py -v`  
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add src/messaging_app/ui/components/ tests/test_message_bubble.py
git commit -m "feat(ui): add MessageBubble component"
```

---

### Task 6: Sidebar Component (Contact List, Search, & Profile Header)

**Files:**
- Create: `src/messaging_app/ui/components/sidebar.py`
- Modify: `src/messaging_app/ui/components/__init__.py`
- Test: `tests/test_sidebar.py`

**Interfaces:**
- Consumes: `messaging_app.models.user.User`, `messaging_app.ui.theme.Theme`, `messaging_app.ui.icons.get_icon`.
- Produces: `Sidebar(master, current_user: User, on_contact_selected: Callable[[User], None], on_add_contact_clicked: Callable[[], None], on_theme_toggle_clicked: Callable[[], None])`.
  - Methods: `set_contacts(contacts: list[User])`, `select_contact(user_id: str)`.

- [ ] **Step 1: Write the failing test**

Write `tests/test_sidebar.py`:
```python
import customtkinter
from messaging_app.models.user import User
from messaging_app.ui.components.sidebar import Sidebar

def test_sidebar_initialization_and_filtering():
    root = customtkinter.CTk()
    me = User("me", "me", "You", "ME", True)
    selected_users: list[User] = []

    sidebar = Sidebar(
        root,
        current_user=me,
        on_contact_selected=lambda u: selected_users.append(u),
        on_add_contact_clicked=lambda: None,
        on_theme_toggle_clicked=lambda: None,
    )

    contacts = [
        User("alice", "alice", "Alice Smith", "AS", True),
        User("bob", "bob", "Bob Martinez", "BM", False),
    ]
    sidebar.set_contacts(contacts)
    assert len(sidebar.get_displayed_contacts()) == 2

    # Test search filter
    sidebar.apply_filter("bob")
    assert len(sidebar.get_displayed_contacts()) == 1
    assert sidebar.get_displayed_contacts()[0].username == "bob"

    root.destroy()
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_sidebar.py -v`  
Expected: FAIL with `ImportError: cannot import name 'Sidebar'`.

- [ ] **Step 3: Implement Sidebar**

Create `src/messaging_app/ui/components/sidebar.py`:
```python
from typing import Callable, Optional
import customtkinter
from messaging_app.models.user import User
from messaging_app.ui.theme import Theme
from messaging_app.ui.icons import get_icon

class Sidebar(customtkinter.CTkFrame):
    """Sidebar featuring current user header, search bar, + Add Contact, and contact cards."""

    def __init__(
        self,
        master: any,
        current_user: User,
        on_contact_selected: Callable[[User], None],
        on_add_contact_clicked: Callable[[], None],
        on_theme_toggle_clicked: Callable[[], None],
        **kwargs
    ) -> None:
        super().__init__(master, width=300, fg_color=Theme.BG_SIDEBAR, corner_radius=0, **kwargs)
        self.grid_propagate(False)

        self._current_user = current_user
        self._on_contact_selected = on_contact_selected
        self._on_add_contact_clicked = on_add_contact_clicked
        self._on_theme_toggle_clicked = on_theme_toggle_clicked

        self._all_contacts: list[User] = []
        self._displayed_contacts: list[User] = []
        self._selected_contact_id: Optional[str] = None
        self._card_widgets: dict[str, customtkinter.CTkFrame] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        # 1. Header Profile & Theme Toggle
        header_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(16, 12))

        avatar_chip = customtkinter.CTkLabel(
            header_frame,
            text=self._current_user.avatar_initials,
            width=36,
            height=36,
            corner_radius=18,
            fg_color=Theme.PRIMARY,
            text_color="#FFFFFF",
            font=(Theme.FONT_FAMILY, 12, "bold"),
        )
        avatar_chip.pack(side="left")

        name_label = customtkinter.CTkLabel(
            header_frame,
            text=self._current_user.display_name,
            font=(Theme.FONT_FAMILY, 14, "bold"),
            text_color=Theme.TEXT_PRIMARY,
        )
        name_label.pack(side="left", padx=10)

        theme_btn = customtkinter.CTkButton(
            header_frame,
            text="",
            image=get_icon("sun", (18, 18)),
            width=36,
            height=36,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.BG_SURFACE,
            hover_color=Theme.BG_HOVER,
            command=self._on_theme_toggle_clicked,
        )
        theme_btn.pack(side="right")

        # 2. Add Contact Button (Hit area: 42px)
        add_btn = customtkinter.CTkButton(
            self,
            text="+ Add Contact",
            image=get_icon("user-plus", (18, 18)),
            compound="left",
            height=Theme.HIT_AREA_HEIGHT,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            font=(Theme.FONT_FAMILY, 13, "bold"),
            command=self._on_add_contact_clicked,
        )
        add_btn.pack(fill="x", padx=16, pady=(0, 10))

        # 3. Search Bar Entry
        search_frame = customtkinter.CTkFrame(self, fg_color=Theme.BG_SURFACE, corner_radius=Theme.RADIUS_INPUT)
        search_frame.pack(fill="x", padx=16, pady=(0, 12))

        search_icon = customtkinter.CTkLabel(search_frame, text="", image=get_icon("search", (16, 16)))
        search_icon.pack(side="left", padx=(10, 4))

        self.search_entry = customtkinter.CTkEntry(
            search_frame,
            placeholder_text="Search contacts...",
            border_width=0,
            fg_color="transparent",
            font=(Theme.FONT_FAMILY, 12),
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=4)
        self.search_entry.bind("<KeyRelease>", lambda e: self.apply_filter(self.search_entry.get()))

        # 4. Scrollable Contact List
        self.contacts_scroll = customtkinter.CTkScrollableFrame(self, fg_color="transparent")
        self.contacts_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def set_contacts(self, contacts: list[User]) -> None:
        self._all_contacts = list(contacts)
        self.apply_filter(self.search_entry.get() if hasattr(self, "search_entry") else "")

    def get_displayed_contacts(self) -> list[User]:
        return list(self._displayed_contacts)

    def apply_filter(self, query: str) -> None:
        q = query.strip().lower()
        if not q:
            self._displayed_contacts = list(self._all_contacts)
        else:
            self._displayed_contacts = [
                c for c in self._all_contacts
                if q in c.display_name.lower() or q in c.username.lower()
            ]
        self._render_contact_cards()

    def _render_contact_cards(self) -> None:
        for widget in self.contacts_scroll.winfo_children():
            widget.destroy()
        self._card_widgets.clear()

        for contact in self._displayed_contacts:
            is_selected = (contact.id == self._selected_contact_id)
            card = customtkinter.CTkFrame(
                self.contacts_scroll,
                corner_radius=Theme.RADIUS_CARD,
                fg_color=Theme.BG_SELECTED if is_selected else Theme.BG_SURFACE,
                cursor="hand2",
                height=56,
            )
            card.pack(fill="x", pady=4, padx=4)
            card.pack_propagate(False)

            # Avatar badge
            avatar = customtkinter.CTkLabel(
                card,
                text=contact.avatar_initials,
                width=36,
                height=36,
                corner_radius=18,
                fg_color=Theme.PRIMARY if is_selected else Theme.BG_HOVER,
                text_color="#FFFFFF" if is_selected else Theme.TEXT_PRIMARY,
                font=(Theme.FONT_FAMILY, 12, "bold"),
            )
            avatar.pack(side="left", padx=(10, 10))

            # Info (Name + Username)
            info_frame = customtkinter.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, pady=8)

            name_lbl = customtkinter.CTkLabel(
                info_frame,
                text=contact.display_name,
                font=(Theme.FONT_FAMILY, 12, "bold"),
                text_color=Theme.TEXT_PRIMARY,
                anchor="w",
            )
            name_lbl.pack(fill="x")

            user_lbl = customtkinter.CTkLabel(
                info_frame,
                text=f"@{contact.username}",
                font=(Theme.FONT_FAMILY, 10),
                text_color=Theme.TEXT_SECONDARY,
                anchor="w",
            )
            user_lbl.pack(fill="x")

            # Online status dot
            status_dot = customtkinter.CTkLabel(
                card,
                text="●",
                font=(Theme.FONT_FAMILY, 12),
                text_color=Theme.STATUS_ONLINE if contact.is_online else Theme.STATUS_OFFLINE,
            )
            status_dot.pack(side="right", padx=12)

            # Click binding
            for w in [card, avatar, info_frame, name_lbl, user_lbl, status_dot]:
                w.bind("<Button-1>", lambda e, c=contact: self._handle_click(c))

            self._card_widgets[contact.id] = card

    def _handle_click(self, contact: User) -> None:
        self.select_contact(contact.id)
        self._on_contact_selected(contact)

    def select_contact(self, user_id: str) -> None:
        self._selected_contact_id = user_id
        for cid, widget in self._card_widgets.items():
            widget.configure(fg_color=Theme.BG_SELECTED if cid == user_id else Theme.BG_SURFACE)
```

Update `src/messaging_app/ui/components/__init__.py`:
```python
from messaging_app.ui.components.message_bubble import MessageBubble
from messaging_app.ui.components.sidebar import Sidebar

__all__ = ["MessageBubble", "Sidebar"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_sidebar.py -v`  
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add src/messaging_app/ui/components/sidebar.py src/messaging_app/ui/components/__init__.py tests/test_sidebar.py
git commit -m "feat(ui): add Sidebar with search, contact list, and header"
```

---

### Task 7: Chat Area & Input Composer

**Files:**
- Create: `src/messaging_app/ui/components/chat_area.py`
- Modify: `src/messaging_app/ui/components/__init__.py`
- Test: `tests/test_chat_area.py`

**Interfaces:**
- Consumes: `messaging_app.models.user.User`, `messaging_app.models.message.Message`, `MessageBubble`, `Theme`, `get_icon`.
- Produces: `ChatArea(master, on_send_message: Callable[[str], None])`.
  - Methods: `set_active_contact(contact: Optional[User])`, `set_messages(messages: list[Message])`, `append_message(message: Message)`.

- [ ] **Step 1: Write the failing test**

Write `tests/test_chat_area.py`:
```python
import customtkinter
from messaging_app.models.user import User
from messaging_app.models.message import Message
from messaging_app.ui.components.chat_area import ChatArea

def test_chat_area_creation_and_messaging():
    root = customtkinter.CTk()
    sent_payloads: list[str] = []

    chat_area = ChatArea(root, on_send_message=lambda text: sent_payloads.append(text))
    alice = User("alice", "alice", "Alice Smith", "AS", True)

    chat_area.set_active_contact(alice)
    assert chat_area.active_contact == alice

    msg = Message("m1", "alice", "me", "Hello from Alice", is_outgoing=False)
    chat_area.append_message(msg)
    assert len(chat_area.get_messages()) == 1

    root.destroy()
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_chat_area.py -v`  
Expected: FAIL with `ImportError: cannot import name 'ChatArea'`.

- [ ] **Step 3: Implement ChatArea**

Create `src/messaging_app/ui/components/chat_area.py`:
```python
from typing import Callable, Optional
import customtkinter
from messaging_app.models.user import User
from messaging_app.models.message import Message
from messaging_app.ui.components.message_bubble import MessageBubble
from messaging_app.ui.theme import Theme
from messaging_app.ui.icons import get_icon

class ChatArea(customtkinter.CTkFrame):
    """Main chat pane containing contact header, message stream, and composer bar."""

    def __init__(self, master: any, on_send_message: Callable[[str], None], **kwargs) -> None:
        super().__init__(master, fg_color=Theme.BG_ROOT, corner_radius=0, **kwargs)
        self.on_send_message = on_send_message

        self.active_contact: Optional[User] = None
        self._messages: list[Message] = []

        self._build_ui()
        self._show_empty_state()

    def _build_ui(self) -> None:
        # 1. Header Bar
        self.header_frame = customtkinter.CTkFrame(
            self, height=64, fg_color=Theme.BG_SURFACE, corner_radius=0
        )
        self.header_frame.pack(fill="x", side="top")
        self.header_frame.pack_propagate(False)

        self.header_avatar = customtkinter.CTkLabel(
            self.header_frame,
            text="",
            width=36,
            height=36,
            corner_radius=18,
            fg_color=Theme.PRIMARY,
            text_color="#FFFFFF",
            font=(Theme.FONT_FAMILY, 12, "bold"),
        )
        self.header_avatar.pack(side="left", padx=(20, 12), pady=14)

        self.header_info = customtkinter.CTkFrame(self.header_frame, fg_color="transparent")
        self.header_info.pack(side="left", fill="y", pady=12)

        self.header_name = customtkinter.CTkLabel(
            self.header_info,
            text="",
            font=(Theme.FONT_FAMILY, 14, "bold"),
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
        )
        self.header_name.pack(anchor="w")

        self.header_status = customtkinter.CTkLabel(
            self.header_info,
            text="",
            font=(Theme.FONT_FAMILY, 11),
            text_color=Theme.STATUS_ONLINE,
            anchor="w",
        )
        self.header_status.pack(anchor="w")

        # 2. Input Composer (Bottom)
        self.composer_frame = customtkinter.CTkFrame(
            self, height=68, fg_color=Theme.BG_SURFACE, corner_radius=0
        )
        self.composer_frame.pack(fill="x", side="bottom")
        self.composer_frame.pack_propagate(False)

        self.input_entry = customtkinter.CTkEntry(
            self.composer_frame,
            placeholder_text="Type a message...",
            height=Theme.HIT_AREA_HEIGHT,
            corner_radius=Theme.RADIUS_INPUT,
            border_width=1,
            border_color=Theme.BORDER,
            font=(Theme.FONT_FAMILY, 13),
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(16, 10), pady=12)
        self.input_entry.bind("<Return>", self._handle_enter)

        self.send_btn = customtkinter.CTkButton(
            self.composer_frame,
            text="",
            image=get_icon("send", (18, 18)),
            width=Theme.HIT_AREA_HEIGHT,
            height=Theme.HIT_AREA_HEIGHT,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._handle_send,
        )
        self.send_btn.pack(side="right", padx=(0, 16), pady=12)

        # 3. Message Stream (Center)
        self.stream_frame = customtkinter.CTkScrollableFrame(self, fg_color="transparent")
        self.stream_frame.pack(fill="both", expand=True, padx=20, pady=12)

    def _show_empty_state(self) -> None:
        for widget in self.stream_frame.winfo_children():
            widget.destroy()

        empty_box = customtkinter.CTkFrame(self.stream_frame, fg_color="transparent")
        empty_box.pack(expand=True, pady=120)

        icon_lbl = customtkinter.CTkLabel(empty_box, text="", image=get_icon("message-square", (48, 48)))
        icon_lbl.pack(pady=(0, 12))

        title = customtkinter.CTkLabel(
            empty_box,
            text="Select a conversation",
            font=(Theme.FONT_FAMILY, 16, "bold"),
            text_color=Theme.TEXT_PRIMARY,
        )
        title.pack()

        subtitle = customtkinter.CTkLabel(
            empty_box,
            text="Choose a contact from the sidebar or add a new user to start messaging.",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_SECONDARY,
        )
        subtitle.pack(pady=4)

    def set_active_contact(self, contact: Optional[User]) -> None:
        self.active_contact = contact
        if not contact:
            self._show_empty_state()
            self.header_name.configure(text="")
            self.header_status.configure(text="")
            self.header_avatar.configure(text="")
            return

        self.header_avatar.configure(text=contact.avatar_initials)
        self.header_name.configure(text=contact.display_name)
        status_text = "● Online" if contact.is_online else "○ Offline"
        status_color = Theme.STATUS_ONLINE if contact.is_online else Theme.STATUS_OFFLINE
        self.header_status.configure(text=status_text, text_color=status_color)
        self.input_entry.focus()

    def set_messages(self, messages: list[Message]) -> None:
        self._messages = list(messages)
        for widget in self.stream_frame.winfo_children():
            widget.destroy()

        initials = self.active_contact.avatar_initials if self.active_contact else "??"
        for msg in self._messages:
            bubble = MessageBubble(self.stream_frame, message=msg, contact_initials=initials)
            bubble.pack(fill="x", pady=4)

        self._scroll_to_bottom()

    def append_message(self, message: Message) -> None:
        self._messages.append(message)
        initials = self.active_contact.avatar_initials if self.active_contact else "??"
        bubble = MessageBubble(self.stream_frame, message=message, contact_initials=initials)
        bubble.pack(fill="x", pady=4)
        self._scroll_to_bottom()

    def get_messages(self) -> list[Message]:
        return list(self._messages)

    def _scroll_to_bottom(self) -> None:
        self.stream_frame.update_idletasks()
        try:
            self.stream_frame._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def _handle_enter(self, event: any) -> None:
        self._handle_send()

    def _handle_send(self) -> None:
        text = self.input_entry.get().strip()
        if text:
            self.input_entry.delete(0, "end")
            self.on_send_message(text)
```

Update `src/messaging_app/ui/components/__init__.py`:
```python
from messaging_app.ui.components.message_bubble import MessageBubble
from messaging_app.ui.components.sidebar import Sidebar
from messaging_app.ui.components.chat_area import ChatArea

__all__ = ["MessageBubble", "Sidebar", "ChatArea"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_chat_area.py -v`  
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add src/messaging_app/ui/components/chat_area.py src/messaging_app/ui/components/__init__.py tests/test_chat_area.py
git commit -m "feat(ui): add ChatArea with header, stream, and composer"
```

---

### Task 8: Add User Modal Dialog

**Files:**
- Create: `src/messaging_app/ui/components/add_user_modal.py`
- Modify: `src/messaging_app/ui/components/__init__.py`
- Test: `tests/test_add_user_modal.py`

**Interfaces:**
- Consumes: `messaging_app.ui.theme.Theme`, `CTkToplevel`.
- Produces: `AddUserModal(parent, on_submit: Callable[[str, str], None])`.

- [ ] **Step 1: Write the failing test**

Write `tests/test_add_user_modal.py`:
```python
import customtkinter
from messaging_app.ui.components.add_user_modal import AddUserModal

def test_add_user_modal_creation():
    root = customtkinter.CTk()
    submitted: list[tuple[str, str]] = []

    modal = AddUserModal(root, on_submit=lambda u, d: submitted.append((u, d)))
    assert modal.title() == "Add New Contact"
    assert modal.winfo_exists()

    # Test error setting
    modal.set_error("Username is required")
    assert modal.error_label.cget("text") == "Username is required"

    modal.destroy()
    root.destroy()
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_add_user_modal.py -v`  
Expected: FAIL with `ImportError: cannot import name 'AddUserModal'`.

- [ ] **Step 3: Implement AddUserModal**

Create `src/messaging_app/ui/components/add_user_modal.py`:
```python
from typing import Callable
import customtkinter
from messaging_app.ui.theme import Theme

class AddUserModal(customtkinter.CTkToplevel):
    """Modal dialog for adding a new user contact with input validation."""

    def __init__(self, master: any, on_submit: Callable[[str, str], None], **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.on_submit = on_submit

        self.title("Add New Contact")
        self.geometry("380x320")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_SURFACE)

        self.transient(master)
        self.grab_set()

        self._build_ui()
        self.center_window()

    def center_window(self) -> None:
        self.update_idletasks()
        parent_x = self.master.winfo_x()
        parent_y = self.master.winfo_y()
        parent_w = self.master.winfo_width()
        parent_h = self.master.winfo_height()

        x = parent_x + (parent_w - 380) // 2
        y = parent_y + (parent_h - 320) // 2
        self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        title_lbl = customtkinter.CTkLabel(
            self,
            text="Add New Contact",
            font=(Theme.FONT_FAMILY, 16, "bold"),
            text_color=Theme.TEXT_PRIMARY,
        )
        title_lbl.pack(pady=(20, 16))

        # Username entry
        user_lbl = customtkinter.CTkLabel(
            self, text="Username (@)", font=(Theme.FONT_FAMILY, 11, "bold"), text_color=Theme.TEXT_SECONDARY, anchor="w"
        )
        user_lbl.pack(fill="x", padx=28, pady=(0, 2))

        self.username_entry = customtkinter.CTkEntry(
            self,
            placeholder_text="e.g. sarah",
            height=Theme.HIT_AREA_HEIGHT,
            corner_radius=Theme.RADIUS_INPUT,
            font=(Theme.FONT_FAMILY, 13),
        )
        self.username_entry.pack(fill="x", padx=28, pady=(0, 12))
        self.username_entry.focus()

        # Display Name entry
        name_lbl = customtkinter.CTkLabel(
            self, text="Display Name", font=(Theme.FONT_FAMILY, 11, "bold"), text_color=Theme.TEXT_SECONDARY, anchor="w"
        )
        name_lbl.pack(fill="x", padx=28, pady=(0, 2))

        self.name_entry = customtkinter.CTkEntry(
            self,
            placeholder_text="e.g. Sarah Connor",
            height=Theme.HIT_AREA_HEIGHT,
            corner_radius=Theme.RADIUS_INPUT,
            font=(Theme.FONT_FAMILY, 13),
        )
        self.name_entry.pack(fill="x", padx=28, pady=(0, 8))

        # Inline error label
        self.error_label = customtkinter.CTkLabel(
            self,
            text="",
            font=(Theme.FONT_FAMILY, 11),
            text_color="#EF4444",
        )
        self.error_label.pack(pady=(0, 12))

        # Buttons row
        btn_row = customtkinter.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=28, pady=(0, 16))

        cancel_btn = customtkinter.CTkButton(
            btn_row,
            text="Cancel",
            height=Theme.HIT_AREA_HEIGHT,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.BG_HOVER,
            hover_color=Theme.BORDER,
            text_color=Theme.TEXT_PRIMARY,
            command=self.destroy,
        )
        cancel_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        submit_btn = customtkinter.CTkButton(
            btn_row,
            text="Add Contact",
            height=Theme.HIT_AREA_HEIGHT,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color="#FFFFFF",
            font=(Theme.FONT_FAMILY, 12, "bold"),
            command=self._handle_submit,
        )
        submit_btn.pack(side="right", fill="x", expand=True, padx=(6, 0))

    def set_error(self, message: str) -> None:
        self.error_label.configure(text=message)

    def _handle_submit(self) -> None:
        username = self.username_entry.get().strip()
        display_name = self.name_entry.get().strip()

        if not username:
            self.set_error("Username is required.")
            return

        self.on_submit(username, display_name)
```

Update `src/messaging_app/ui/components/__init__.py`:
```python
from messaging_app.ui.components.message_bubble import MessageBubble
from messaging_app.ui.components.sidebar import Sidebar
from messaging_app.ui.components.chat_area import ChatArea
from messaging_app.ui.components.add_user_modal import AddUserModal

__all__ = ["MessageBubble", "Sidebar", "ChatArea", "AddUserModal"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_add_user_modal.py -v`  
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add src/messaging_app/ui/components/add_user_modal.py src/messaging_app/ui/components/__init__.py tests/test_add_user_modal.py
git commit -m "feat(ui): add AddUserModal dialog with validation"
```

---

### Task 9: Main Application Window & Entry Point Integration

**Files:**
- Create: `src/messaging_app/ui/app.py`
- Create: `src/messaging_app/main.py`
- Test: `tests/test_app_integration.py`

**Interfaces:**
- Consumes: `MessagingServiceProtocol`, `DummyMessagingService`, `Sidebar`, `ChatArea`, `AddUserModal`, `Theme`.
- Produces: `MessagingApp(customtkinter.CTk)` wired to the messaging service and executable main entry point.

- [ ] **Step 1: Write the failing integration test**

Write `tests/test_app_integration.py`:
```python
import time
import customtkinter
from messaging_app.services.dummy_service import DummyMessagingService
from messaging_app.ui.app import MessagingApp

def test_app_integration_flow():
    service = DummyMessagingService(simulation_delay=0.05)
    app = MessagingApp(service=service)

    # Initial state check
    assert len(app.sidebar.get_displayed_contacts()) >= 3
    alice = app.sidebar.get_displayed_contacts()[0]

    # Select contact
    app.select_contact(alice)
    assert app.chat_area.active_contact.id == alice.id

    # Send message through app
    app.handle_send_message("Integration test hello!")
    history = service.get_messages(alice.id)
    assert any(m.content == "Integration test hello!" for m in history)

    # Add contact through app
    new_user = app.handle_add_contact("eva", "Eva Green")
    assert new_user.username == "eva"
    assert any(c.username == "eva" for c in app.sidebar.get_displayed_contacts())

    app.destroy()
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_app_integration.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'messaging_app.ui.app'`.

- [ ] **Step 3: Implement MessagingApp and main.py**

Create `src/messaging_app/ui/app.py`:
```python
from typing import Optional
import customtkinter
from messaging_app.models.user import User
from messaging_app.models.message import Message
from messaging_app.services.protocol import MessagingServiceProtocol
from messaging_app.ui.components.sidebar import Sidebar
from messaging_app.ui.components.chat_area import ChatArea
from messaging_app.ui.components.add_user_modal import AddUserModal
from messaging_app.ui.theme import Theme

class MessagingApp(customtkinter.CTk):
    """Main Application Window coordinating Sidebar, ChatArea, and MessagingService."""

    def __init__(self, service: MessagingServiceProtocol, **kwargs) -> None:
        super().__init__(**kwargs)
        self.service = service

        self.title("NexusChat — Python Messaging App")
        self.geometry("1024x720")
        self.minsize(880, 580)
        self.configure(fg_color=Theme.BG_ROOT)

        # Set default appearance mode (Dark Slate)
        customtkinter.set_appearance_mode("Dark")
        customtkinter.set_default_color_theme("blue")

        self._active_contact: Optional[User] = None
        self._modal_instance: Optional[AddUserModal] = None

        self._setup_layout()
        self._subscribe_to_service()
        self._load_initial_data()

    def _setup_layout(self) -> None:
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar (Fixed 300px width)
        self.sidebar = Sidebar(
            self,
            current_user=self.service.get_current_user(),
            on_contact_selected=self.select_contact,
            on_add_contact_clicked=self.open_add_contact_dialog,
            on_theme_toggle_clicked=self.toggle_theme,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Chat Area (Expands)
        self.chat_area = ChatArea(
            self,
            on_send_message=self.handle_send_message,
        )
        self.chat_area.grid(row=0, column=1, sticky="nsew")

    def _subscribe_to_service(self) -> None:
        self.service.subscribe_message_received(self._on_message_received_async)
        self.service.subscribe_contact_added(self._on_contact_added_async)

    def _load_initial_data(self) -> None:
        contacts = self.service.get_contacts()
        self.sidebar.set_contacts(contacts)
        if contacts:
            self.select_contact(contacts[0])

    def select_contact(self, contact: User) -> None:
        self._active_contact = contact
        self.sidebar.select_contact(contact.id)
        self.chat_area.set_active_contact(contact)
        messages = self.service.get_messages(contact.id)
        self.chat_area.set_messages(messages)

    def handle_send_message(self, text: str) -> None:
        if not self._active_contact:
            return
        msg = self.service.send_message(self._active_contact.id, text)
        self.chat_area.append_message(msg)

    def _on_message_received_async(self, message: Message) -> None:
        """Ensure thread-safe GUI updates via after()."""
        self.after(0, self._handle_incoming_message_ui, message)

    def _handle_incoming_message_ui(self, message: Message) -> None:
        if self._active_contact and message.sender_id == self._active_contact.id:
            self.chat_area.append_message(message)

    def _on_contact_added_async(self, user: User) -> None:
        self.after(0, self._handle_contact_added_ui, user)

    def _handle_contact_added_ui(self, user: User) -> None:
        self.sidebar.set_contacts(self.service.get_contacts())
        self.select_contact(user)

    def open_add_contact_dialog(self) -> None:
        if self._modal_instance and self._modal_instance.winfo_exists():
            self._modal_instance.focus()
            return
        self._modal_instance = AddUserModal(self, on_submit=self._handle_modal_submit)

    def _handle_modal_submit(self, username: str, display_name: str) -> None:
        try:
            self.handle_add_contact(username, display_name)
            if self._modal_instance and self._modal_instance.winfo_exists():
                self._modal_instance.destroy()
                self._modal_instance = None
        except ValueError as err:
            if self._modal_instance and self._modal_instance.winfo_exists():
                self._modal_instance.set_error(str(err))

    def handle_add_contact(self, username: str, display_name: str) -> User:
        return self.service.add_contact(username, display_name)

    def toggle_theme(self) -> None:
        current = customtkinter.get_appearance_mode()
        new_mode = "Light" if current == "Dark" else "Dark"
        customtkinter.set_appearance_mode(new_mode)
```

Create `src/messaging_app/main.py`:
```python
from messaging_app.services.dummy_service import DummyMessagingService
from messaging_app.ui.app import MessagingApp

def main() -> None:
    service = DummyMessagingService(simulation_delay=1.2)
    app = MessagingApp(service=service)
    app.mainloop()

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run integration test to verify it passes**

Run: `pytest tests/test_app_integration.py -v`  
Expected: PASS (1 passed).

- [ ] **Step 5: Commit**

```bash
git add src/messaging_app/ui/app.py src/messaging_app/main.py tests/test_app_integration.py
git commit -m "feat: complete root MessagingApp window and main entry point"
```

---

### Task 10: Full Test Suite Verification, Documentation & Verification Pass

**Files:**
- Create: `README.md`
- Test: All unit and integration tests across the project.

**Interfaces:**
- Consumes: Complete project codebase.
- Produces: 100% passing test suite and comprehensive developer documentation.

- [ ] **Step 1: Run the full test suite**

Run: `pytest -v`  
Expected: All tests pass (10+ tests).

- [ ] **Step 2: Create comprehensive README.md**

Write `README.md` documenting:
- Project overview & features
- Architecture & decoupled service design
- How to install requirements and run the app
- How to trigger dummy features (sending, simulated replies, adding contacts)
- How to swap dummy service with real networking

- [ ] **Step 3: Verification run of the application**

Run: `python -m src.messaging_app.main --help` or headless run test to verify zero syntax/runtime errors.

- [ ] **Step 4: Final commit**

```bash
git add README.md
git commit -m "docs: add comprehensive README and finalize implementation"
```
