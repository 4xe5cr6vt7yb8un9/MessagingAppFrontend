"""Chat area component containing contact header, message stream, and input composer."""

from typing import Any, Callable, Optional
import customtkinter

from messaging_app.models.message import Message
from messaging_app.models.user import User
from messaging_app.ui.components.message_bubble import MessageBubble
from messaging_app.ui.icons import get_icon
from messaging_app.ui.theme import Theme


class ChatArea(customtkinter.CTkFrame):
    """Main chat pane containing contact header, message stream, and composer bar."""

    def __init__(
        self,
        master: Any,
        on_send_message: Callable[[str], None],
        **kwargs: Any,
    ) -> None:
        """Initialize ChatArea with header bar, message stream, and composer."""
        super().__init__(master, fg_color=Theme.BG_ROOT, corner_radius=0, **kwargs)
        self.on_send_message = on_send_message

        self.active_contact: Optional[User] = None
        self._messages: list[Message] = []
        self._empty_box: Optional[customtkinter.CTkFrame] = None

        self.header_frame: customtkinter.CTkFrame
        self.header_avatar: customtkinter.CTkLabel
        self.header_info: customtkinter.CTkFrame
        self.header_name: customtkinter.CTkLabel
        self.header_status: customtkinter.CTkLabel
        self.composer_frame: customtkinter.CTkFrame
        self.input_entry: customtkinter.CTkEntry
        self.send_btn: customtkinter.CTkButton
        self.stream_frame: customtkinter.CTkScrollableFrame

        self._build_ui()
        self._show_empty_state()

    def _build_ui(self) -> None:
        """Construct header bar, composer bar, and message stream layouts."""
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
        """Display placeholder graphic and guidance when no conversation is active."""
        for widget in self.stream_frame.winfo_children():
            widget.destroy()

        self._empty_box = customtkinter.CTkFrame(self.stream_frame, fg_color="transparent")
        self._empty_box.pack(expand=True, pady=120)

        icon_lbl = customtkinter.CTkLabel(
            self._empty_box, text="", image=get_icon("message-square", (48, 48))
        )
        icon_lbl.pack(pady=(0, 12))

        title = customtkinter.CTkLabel(
            self._empty_box,
            text="Select a conversation",
            font=(Theme.FONT_FAMILY, 16, "bold"),
            text_color=Theme.TEXT_PRIMARY,
        )
        title.pack()

        subtitle = customtkinter.CTkLabel(
            self._empty_box,
            text="Choose a contact from the sidebar or add a new user to start messaging.",
            font=(Theme.FONT_FAMILY, 12),
            text_color=Theme.TEXT_SECONDARY,
        )
        subtitle.pack(pady=4)

    def _clear_empty_state(self) -> None:
        """Remove placeholder empty card if present."""
        if self._empty_box is not None:
            self._empty_box.destroy()
            self._empty_box = None

    def set_active_contact(self, contact: Optional[User]) -> None:
        """Update active contact header and focus entry or show empty state."""
        self.active_contact = contact
        if not contact:
            self._messages = []
            self._show_empty_state()
            self.header_name.configure(text="")
            self.header_status.configure(text="")
            self.header_avatar.configure(text="")
            return

        self._clear_empty_state()
        self.header_avatar.configure(text=contact.avatar_initials)
        self.header_name.configure(text=contact.display_name)
        status_text = "● Online" if contact.is_online else "○ Offline"
        status_color = Theme.STATUS_ONLINE if contact.is_online else Theme.STATUS_OFFLINE
        self.header_status.configure(text=status_text, text_color=status_color)
        self.input_entry.focus()

    def update_presence(self, user_id: str, is_online: bool) -> None:
        """Update active contact status indicator if matching user_id."""
        if self.active_contact and self.active_contact.id == user_id:
            import dataclasses

            self.active_contact = dataclasses.replace(self.active_contact, is_online=is_online)
            status_text = "● Online" if is_online else "○ Offline"
            status_color = Theme.STATUS_ONLINE if is_online else Theme.STATUS_OFFLINE
            self.header_status.configure(text=status_text, text_color=status_color)

    def set_messages(self, messages: list[Message]) -> None:
        """Populate message stream with provided messages list."""
        self._messages = list(messages)
        self._empty_box = None
        for widget in self.stream_frame.winfo_children():
            widget.destroy()

        initials = self.active_contact.avatar_initials if self.active_contact else "??"
        for msg in self._messages:
            bubble = MessageBubble(self.stream_frame, message=msg, contact_initials=initials)
            bubble.pack(fill="x", pady=4)

        self._scroll_to_bottom()

    def append_message(self, message: Message) -> None:
        """Append a single message bubble to stream and auto-scroll to bottom."""
        self._clear_empty_state()
        self._messages.append(message)
        initials = self.active_contact.avatar_initials if self.active_contact else "??"
        bubble = MessageBubble(self.stream_frame, message=message, contact_initials=initials)
        bubble.pack(fill="x", pady=4)
        self._scroll_to_bottom()

    def get_messages(self) -> list[Message]:
        """Return a shallow copy of messages currently in the stream."""
        return list(self._messages)

    def _scroll_to_bottom(self) -> None:
        """Scroll stream canvas down to latest message."""
        self.stream_frame.update_idletasks()
        try:
            self.stream_frame._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def _handle_enter(self, event: Any = None) -> None:
        """Handle enter keypress in composer entry."""
        self._handle_send()

    def _handle_send(self) -> None:
        """Extract input text, clear entry, and invoke message send callback."""
        text = self.input_entry.get().strip()
        if text:
            self.input_entry.delete(0, "end")
            self.on_send_message(text)
