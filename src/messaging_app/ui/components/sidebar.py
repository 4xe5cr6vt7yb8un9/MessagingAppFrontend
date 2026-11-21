"""Sidebar component featuring user header, search, add-contact button, and contact list."""

import dataclasses
from typing import Any, Callable, Optional
import customtkinter

from messaging_app.models.user import User
from messaging_app.ui.icons import get_icon
from messaging_app.ui.theme import Theme


class Sidebar(customtkinter.CTkFrame):
    """Sidebar featuring current user header, search bar, + Add Contact, and contact cards."""

    def __init__(
        self,
        master: Any,
        current_user: User,
        on_contact_selected: Callable[[User], None],
        on_add_contact_clicked: Callable[[], None],
        on_theme_toggle_clicked: Callable[[], None],
        **kwargs: Any,
    ) -> None:
        """Initialize Sidebar with user header, search input, action button, and contact list."""
        super().__init__(master, width=300, fg_color=Theme.BG_SIDEBAR, corner_radius=0, **kwargs)
        self.grid_propagate(False)

        self._current_user: User = current_user
        self._on_contact_selected: Callable[[User], None] = on_contact_selected
        self._on_add_contact_clicked: Callable[[], None] = on_add_contact_clicked
        self._on_theme_toggle_clicked: Callable[[], None] = on_theme_toggle_clicked

        self._all_contacts: list[User] = []
        self._displayed_contacts: list[User] = []
        self._selected_contact_id: Optional[str] = None
        self._card_widgets: dict[str, customtkinter.CTkFrame] = {}
        self._avatar_widgets: dict[str, customtkinter.CTkLabel] = {}
        self._status_dot_widgets: dict[str, customtkinter.CTkLabel] = {}

        self.theme_btn: customtkinter.CTkButton
        self.add_btn: customtkinter.CTkButton
        self.search_entry: customtkinter.CTkEntry
        self.contacts_scroll: customtkinter.CTkScrollableFrame
        self.connection_pill: customtkinter.CTkLabel

        self._build_ui()

    def _build_ui(self) -> None:
        """Construct the sidebar layout sections."""
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

        user_info = customtkinter.CTkFrame(header_frame, fg_color="transparent")
        user_info.pack(side="left", padx=10)

        name_label = customtkinter.CTkLabel(
            user_info,
            text=self._current_user.display_name,
            font=(Theme.FONT_FAMILY, 14, "bold"),
            text_color=Theme.TEXT_PRIMARY,
            anchor="w",
        )
        name_label.pack(anchor="w")

        self.connection_pill = customtkinter.CTkLabel(
            user_info,
            text="✕ Disconnected",
            font=(Theme.FONT_FAMILY, 10),
            text_color="#EF4444",
            anchor="w",
        )
        self.connection_pill.pack(anchor="w")

        self.theme_btn = customtkinter.CTkButton(
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
        self.theme_btn.pack(side="right")

        # 2. Add Contact Button (Hit area: 42px)
        self.add_btn = customtkinter.CTkButton(
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
        self.add_btn.pack(fill="x", padx=16, pady=(0, 10))

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
        """Update contacts list and re-apply active search filter."""
        self._all_contacts = list(contacts)
        query = self.search_entry.get() if hasattr(self, "search_entry") else ""
        self.apply_filter(query)

    def get_displayed_contacts(self) -> list[User]:
        """Return defensive copy of currently displayed contacts."""
        return list(self._displayed_contacts)

    def apply_filter(self, query: str) -> None:
        """Filter displayed contacts based on case-insensitive display name or username match."""
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
        """Render contact cards in the scrollable contact list frame."""
        for widget in self.contacts_scroll.winfo_children():
            widget.destroy()
        self._card_widgets.clear()
        self._avatar_widgets.clear()
        self._status_dot_widgets.clear()

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

            self._card_widgets[contact.id] = card
            self._avatar_widgets[contact.id] = avatar
            self._status_dot_widgets[contact.id] = status_dot

            # Event bindings for clicking and hover states
            interactive_widgets = [card, avatar, info_frame, name_lbl, user_lbl, status_dot]
            for w in interactive_widgets:
                w.bind("<Button-1>", lambda e, c=contact: self._handle_click(c))
                w.bind("<Enter>", lambda e, cid=contact.id: self._on_card_hover_enter(cid, e))
                w.bind("<Leave>", lambda e, cid=contact.id: self._on_card_hover_leave(cid, e))

    def _handle_click(self, contact: User) -> None:
        """Handle contact card selection."""
        self.select_contact(contact.id)
        self._on_contact_selected(contact)

    def set_connection_status(self, status: str, detail: str = "") -> None:
        """Update connection indicator text and color based on network status."""
        st = (status or "").upper()
        if st == "CONNECTED":
            text = "● Connected"
            color = "#10B981"
        elif st == "RECONNECTING":
            text = "○ Reconnecting..."
            color = "#F59E0B"
        else:
            text = "✕ Disconnected"
            color = "#EF4444"

        if hasattr(self, "connection_pill") and self.connection_pill.winfo_exists():
            self.connection_pill.configure(text=text, text_color=color)

    def update_presence(self, user_id: str, is_online: bool) -> None:
        """Update presence status for a contact in sidebar cards and stored contact objects."""
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        self._all_contacts = [
            dataclasses.replace(c, is_online=is_online) if c.id == user_id else c
            for c in self._all_contacts
        ]
        self._displayed_contacts = [
            dataclasses.replace(c, is_online=is_online) if c.id == user_id else c
            for c in self._displayed_contacts
        ]

        dot = self._status_dot_widgets.get(user_id)
        if dot and dot.winfo_exists():
            dot.configure(
                text_color=Theme.STATUS_ONLINE if is_online else Theme.STATUS_OFFLINE
            )

    def select_contact(self, user_id: str) -> None:
        """Update selection state and visual appearance of contact cards."""
        self._selected_contact_id = user_id
        for cid, widget in self._card_widgets.items():
            is_selected = (cid == user_id)
            widget.configure(fg_color=Theme.BG_SELECTED if is_selected else Theme.BG_SURFACE)
            avatar = self._avatar_widgets.get(cid)
            if avatar:
                avatar.configure(
                    fg_color=Theme.PRIMARY if is_selected else Theme.BG_HOVER,
                    text_color="#FFFFFF" if is_selected else Theme.TEXT_PRIMARY,
                )

    def _on_card_hover_enter(self, contact_id: str, event: Any = None) -> None:
        """Handle mouse enter on contact card or child widget."""
        if self._selected_contact_id == contact_id:
            return
        card = self._card_widgets.get(contact_id)
        if card:
            card.configure(fg_color=Theme.BG_HOVER)

    def _on_card_hover_leave(self, contact_id: str, event: Any = None) -> None:
        """Handle mouse leave on contact card or child widget."""
        if self._selected_contact_id == contact_id:
            return
        card = self._card_widgets.get(contact_id)
        if not card or not card.winfo_exists():
            return
        if event is not None and hasattr(event, "x_root") and hasattr(event, "y_root"):
            try:
                x, y = event.x_root, event.y_root
                card_x = card.winfo_rootx()
                card_y = card.winfo_rooty()
                card_w = card.winfo_width()
                card_h = card.winfo_height()
                if card_x <= x <= card_x + card_w and card_y <= y <= card_y + card_h:
                    return
            except Exception:
                pass
        card.configure(fg_color=Theme.BG_SURFACE)
