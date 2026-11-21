"""Main Application Window coordinating Sidebar, ChatArea, and MessagingService."""

from typing import Any, Optional
import customtkinter

from messaging_app.models.message import Message
from messaging_app.models.user import User
from messaging_app.services.protocol import MessagingServiceProtocol
from messaging_app.ui.components.add_user_modal import AddUserModal
from messaging_app.ui.components.chat_area import ChatArea
from messaging_app.ui.components.sidebar import Sidebar
from messaging_app.ui.icons import get_icon
from messaging_app.ui.theme import Theme


class MessagingApp(customtkinter.CTk):
    """Main Application Window coordinating Sidebar, ChatArea, and MessagingService."""

    def __init__(self, service: MessagingServiceProtocol, **kwargs: Any) -> None:
        """Initialize main application window, configure layouts, and wire service events."""
        super().__init__(**kwargs)
        import tkinter
        tkinter._default_root = self
        self.service: MessagingServiceProtocol = service

        self.title("NexusChat — Python Messaging App")
        self.geometry("1024x720")
        self.minsize(880, 580)
        self.configure(fg_color=Theme.BG_ROOT)

        # Set default appearance mode (Dark)
        customtkinter.set_appearance_mode("Dark")
        customtkinter.set_default_color_theme("blue")

        self._active_contact: Optional[User] = None
        self._modal_instance: Optional[AddUserModal] = None

        self.sidebar: Sidebar
        self.chat_area: ChatArea

        self._setup_layout()
        self._subscribe_to_service()
        self._load_initial_data()

    def _setup_layout(self) -> None:
        """Configure two-column grid layout with fixed sidebar and expanding chat area."""
        self.grid_columnconfigure(0, weight=0, minsize=300)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar (300px fixed width)
        self.sidebar = Sidebar(
            self,
            current_user=self.service.get_current_user(),
            on_contact_selected=self.select_contact,
            on_add_contact_clicked=self.open_add_contact_dialog,
            on_theme_toggle_clicked=self.toggle_theme,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Chat Area (Expands to fill remaining window)
        self.chat_area = ChatArea(
            self,
            on_send_message=self.handle_send_message,
        )
        self.chat_area.grid(row=0, column=1, sticky="nsew")

    def _subscribe_to_service(self) -> None:
        """Register callbacks for service-level asynchronous events."""
        self.service.subscribe_message_received(self._on_message_received_async)
        self.service.subscribe_contact_added(self._on_contact_added_async)

        if hasattr(self.service, "subscribe_connection_status"):
            self.service.subscribe_connection_status(self._on_connection_status_async)

        if hasattr(self.service, "subscribe_presence_updated"):
            self.service.subscribe_presence_updated(self._on_presence_updated_async)

    def _load_initial_data(self) -> None:
        """Load contacts from service into sidebar and select the first active contact."""
        contacts = self.service.get_contacts()
        self.sidebar.set_contacts(contacts)
        if contacts:
            self.select_contact(contacts[0])

    def select_contact(self, contact: User) -> None:
        """Switch active conversation, update sidebar selection, and populate message history."""
        self._active_contact = contact
        self.sidebar.select_contact(contact.id)
        self.chat_area.set_active_contact(contact)
        messages = self.service.get_messages(contact.id)
        self.chat_area.set_messages(messages)

    def handle_send_message(self, text: str) -> None:
        """Dispatch outgoing message via service and append to conversation stream."""
        if not self._active_contact:
            return
        msg = self.service.send_message(self._active_contact.id, text)
        self.chat_area.append_message(msg)

    def _on_message_received_async(self, message: Message) -> None:
        """Ensure thread-safe GUI updates for incoming messages via after()."""
        try:
            if self.winfo_exists():
                self.after(0, self._handle_incoming_message_ui, message)
        except Exception:
            pass

    def _handle_incoming_message_ui(self, message: Message) -> None:
        """Append incoming message to chat stream if it belongs to currently active contact."""
        if self._active_contact and message.sender_id == self._active_contact.id:
            self.chat_area.append_message(message)

    def _on_contact_added_async(self, user: User) -> None:
        """Ensure thread-safe GUI updates for newly added contacts via after()."""
        try:
            if self.winfo_exists():
                self.after(0, self._handle_contact_added_ui, user)
        except Exception:
            pass

    def _handle_contact_added_ui(self, user: User) -> None:
        """Refresh contacts list in sidebar and auto-select the newly added contact."""
        self.sidebar.set_contacts(self.service.get_contacts())
        self.select_contact(user)

    def _on_connection_status_async(self, status: str, detail: str = "") -> None:
        """Ensure thread-safe GUI updates for connection status transitions."""
        try:
            if self.winfo_exists():
                self.after(0, self.sidebar.set_connection_status, status, detail)
        except Exception:
            pass

    def _on_presence_updated_async(self, user_id: str, is_online: bool) -> None:
        """Ensure thread-safe GUI updates for contact presence updates."""
        try:
            if self.winfo_exists():
                self.after(0, self._handle_presence_update_ui, user_id, is_online)
        except Exception:
            pass

    def _handle_presence_update_ui(self, user_id: str, is_online: bool) -> None:
        """Update contact presence dot in sidebar and chat header."""
        import dataclasses

        if hasattr(self, "sidebar") and hasattr(self.sidebar, "update_presence"):
            self.sidebar.update_presence(user_id, is_online)
        if self._active_contact and self._active_contact.id == user_id:
            self._active_contact = dataclasses.replace(self._active_contact, is_online=is_online)
        if hasattr(self, "chat_area") and hasattr(self.chat_area, "update_presence"):
            self.chat_area.update_presence(user_id, is_online)

    def open_add_contact_dialog(self) -> None:
        """Open contact creation modal dialog, focusing existing instance if already open."""
        if self._modal_instance and self._modal_instance.winfo_exists():
            self._modal_instance.focus()
            return
        self._modal_instance = AddUserModal(self, on_submit=self._handle_modal_submit)

    def _handle_modal_submit(self, username: str, display_name: str) -> None:
        """Handle contact creation attempt from modal dialog with error feedback."""
        try:
            self.handle_add_contact(username, display_name)
            if self._modal_instance and self._modal_instance.winfo_exists():
                self._modal_instance.destroy()
                self._modal_instance = None
        except ValueError as err:
            if self._modal_instance and self._modal_instance.winfo_exists():
                self._modal_instance.set_error(str(err))

    def handle_add_contact(self, username: str, display_name: str) -> User:
        """Create a new contact in the service layer."""
        user = self.service.add_contact(username, display_name)
        try:
            if self.winfo_exists():
                self.update()
        except Exception:
            pass
        return user

    def toggle_theme(self) -> None:
        """Toggle appearance mode between Dark and Light."""
        current = customtkinter.get_appearance_mode()
        new_mode = "Light" if current == "Dark" else "Dark"
        customtkinter.set_appearance_mode(new_mode)
        if hasattr(self, "sidebar") and hasattr(self.sidebar, "theme_btn") and self.sidebar.theme_btn.winfo_exists():
            icon_name = "moon" if new_mode == "Light" else "sun"
            self.sidebar.theme_btn.configure(image=get_icon(icon_name, (18, 18)))
