"""Modal dialog for adding new user contacts."""

from typing import Any, Callable

import customtkinter

from messaging_app.ui.theme import Theme


class AddUserModal(customtkinter.CTkToplevel):
    """Modal dialog for adding a new user contact with input validation."""

    def __init__(
        self,
        master: Any,
        on_submit: Callable[[str, str], None],
        **kwargs: Any,
    ) -> None:
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
        """Center modal dialog window over the master window."""
        self.update_idletasks()
        if self.master:
            parent_x = self.master.winfo_x()
            parent_y = self.master.winfo_y()
            parent_w = self.master.winfo_width()
            parent_h = self.master.winfo_height()

            x = max(0, parent_x + (parent_w - 380) // 2)
            y = max(0, parent_y + (parent_h - 320) // 2)
            self.geometry(f"+{x}+{y}")

    def _build_ui(self) -> None:
        """Construct dialog input fields, validation labels, and action buttons."""
        title_lbl = customtkinter.CTkLabel(
            self,
            text="Add New Contact",
            font=(Theme.FONT_FAMILY, 16, "bold"),
            text_color=Theme.TEXT_PRIMARY,
        )
        title_lbl.pack(pady=(20, 16))

        # Username entry
        user_lbl = customtkinter.CTkLabel(
            self,
            text="Username (@)",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
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
        self.username_entry.bind("<Return>", self._handle_return)
        self.username_entry.focus()

        # Display Name entry
        name_lbl = customtkinter.CTkLabel(
            self,
            text="Display Name",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_SECONDARY,
            anchor="w",
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
        self.name_entry.bind("<Return>", self._handle_return)

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

        self.cancel_btn = customtkinter.CTkButton(
            btn_row,
            text="Cancel",
            height=Theme.HIT_AREA_HEIGHT,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.BG_HOVER,
            hover_color=Theme.BORDER,
            text_color=Theme.TEXT_PRIMARY,
            command=self.destroy,
        )
        self.cancel_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.submit_btn = customtkinter.CTkButton(
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
        self.submit_btn.pack(side="right", fill="x", expand=True, padx=(6, 0))

        # Keyboard shortcuts
        self.bind("<Escape>", self._handle_escape)

    def set_error(self, message: str) -> None:
        """Display validation error message inline in red text."""
        self.error_label.configure(text=message)

    def _handle_return(self, _event: Any = None) -> None:
        """Handle Return key press in entry fields to submit form."""
        self._handle_submit()

    def _handle_escape(self, _event: Any = None) -> None:
        """Handle Escape key press to cancel and dismiss modal."""
        self.destroy()

    def _handle_submit(self) -> None:
        """Validate input values and invoke on_submit callback."""
        username = self.username_entry.get().strip()
        display_name = self.name_entry.get().strip()

        if not username:
            self.set_error("Username is required.")
            return

        self.on_submit(username, display_name)
