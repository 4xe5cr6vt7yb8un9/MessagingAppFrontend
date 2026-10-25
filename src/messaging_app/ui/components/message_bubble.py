"""Message bubble component for chat messages."""

from typing import Any, Optional
import customtkinter

from messaging_app.models.message import Message
from messaging_app.ui.theme import Theme


class MessageBubble(customtkinter.CTkFrame):
    """A stylized message bubble following concentric radius and optical alignment rules."""

    def __init__(
        self,
        master: Any,
        message: Message,
        contact_initials: str = "",
        **kwargs: Any,
    ) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.message = message
        self.avatar: Optional[customtkinter.CTkLabel] = None

        is_out = message.is_outgoing
        time_str = message.timestamp.strftime("%I:%M %p")

        # Container frame
        self.bubble_frame = customtkinter.CTkFrame(
            self,
            corner_radius=Theme.RADIUS_CARD,
            fg_color=Theme.BUBBLE_OUT if is_out else Theme.BUBBLE_IN,
            border_width=0 if is_out else 1,
            border_color=Theme.BORDER,
        )

        # Avatar for incoming message
        if not is_out:
            self.avatar = customtkinter.CTkLabel(
                self,
                text=contact_initials or "??",
                width=32,
                height=32,
                corner_radius=16,
                fg_color=Theme.PRIMARY,
                text_color="#FFFFFF",
                font=(Theme.FONT_FAMILY, 11, "bold"),
            )
            self.avatar.pack(side="left", anchor="e", padx=(0, 8), pady=(0, 4))
            self.bubble_frame.pack(side="left", anchor="w", padx=(0, 40))
        else:
            self.bubble_frame.pack(side="right", anchor="e", padx=(40, 0))

        # Message text label
        self.text_label = customtkinter.CTkLabel(
            self.bubble_frame,
            text=message.content,
            text_color=Theme.TEXT_ON_PRIMARY if is_out else Theme.TEXT_PRIMARY,
            font=(Theme.FONT_FAMILY, 13),
            wraplength=420,
            justify="left",
            anchor="w",
        )
        self.text_label.pack(padx=12, pady=(8, 2), anchor="w")

        # Timestamp row
        self.time_label = customtkinter.CTkLabel(
            self.bubble_frame,
            text=time_str,
            text_color="#CBD5E1" if is_out else Theme.TEXT_SECONDARY,
            font=(Theme.FONT_FAMILY, 10),
        )
        self.time_label.pack(padx=12, pady=(0, 6), anchor="e")
