"""Unit tests for Sidebar component."""

from pathlib import Path
import sys
from unittest.mock import MagicMock

import customtkinter
import pytest

# Ensure src is in sys.path for standalone pytest invocations
_SRC_PATH = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_PATH not in sys.path:
    sys.path.insert(0, _SRC_PATH)

from messaging_app.models.user import User
from messaging_app.ui.components import Sidebar
from messaging_app.ui.components.sidebar import Sidebar as DirectSidebar
from messaging_app.ui.icons import _ICON_CACHE
from messaging_app.ui.theme import Theme


@pytest.fixture(autouse=True)
def _clean_icons_and_tk():
    """Ensure clean icon cache before and after each test."""
    _ICON_CACHE.clear()
    yield
    _ICON_CACHE.clear()


def test_components_package_exports() -> None:
    """Verify that components __init__ exposes Sidebar."""
    assert Sidebar is DirectSidebar


def test_sidebar_initialization_and_filtering() -> None:
    """Verify initialization, contact population, and search filtering."""
    root = customtkinter.CTk()
    try:
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

        # Test search filter by display name (case-insensitive)
        sidebar.apply_filter("ALICE")
        assert len(sidebar.get_displayed_contacts()) == 1
        assert sidebar.get_displayed_contacts()[0].username == "alice"

        # Test search filter empty string resets list
        sidebar.apply_filter("")
        assert len(sidebar.get_displayed_contacts()) == 2

        # Test non-matching query
        sidebar.apply_filter("nonexistent")
        assert len(sidebar.get_displayed_contacts()) == 0
    finally:
        root.destroy()


def test_sidebar_contact_selection_and_callbacks() -> None:
    """Verify contact selection updates state and invokes callback."""
    root = customtkinter.CTk()
    try:
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

        # Select Alice directly
        sidebar.select_contact("alice")
        assert sidebar._selected_contact_id == "alice"
        assert sidebar._card_widgets["alice"].cget("fg_color") == Theme.BG_SELECTED
        assert sidebar._card_widgets["bob"].cget("fg_color") == Theme.BG_SURFACE

        # Simulate click on Bob
        sidebar._handle_click(contacts[1])
        assert len(selected_users) == 1
        assert selected_users[0].id == "bob"
        assert sidebar._selected_contact_id == "bob"
        assert sidebar._card_widgets["bob"].cget("fg_color") == Theme.BG_SELECTED
        assert sidebar._card_widgets["alice"].cget("fg_color") == Theme.BG_SURFACE
    finally:
        root.destroy()


def test_sidebar_action_buttons() -> None:
    """Verify Add Contact and Theme Toggle callbacks."""
    root = customtkinter.CTk()
    try:
        me = User("me", "me", "You", "ME", True)
        add_clicked = MagicMock()
        theme_clicked = MagicMock()

        sidebar = Sidebar(
            root,
            current_user=me,
            on_contact_selected=lambda u: None,
            on_add_contact_clicked=add_clicked,
            on_theme_toggle_clicked=theme_clicked,
        )

        # Trigger Add Contact button command
        sidebar.add_btn.invoke()
        assert add_clicked.call_count == 1

        # Trigger Theme Toggle button command
        sidebar.theme_btn.invoke()
        assert theme_clicked.call_count == 1
    finally:
        root.destroy()


def test_sidebar_hover_states() -> None:
    """Verify hover enter and leave update background color for unselected card."""
    root = customtkinter.CTk()
    try:
        me = User("me", "me", "You", "ME", True)
        sidebar = Sidebar(
            root,
            current_user=me,
            on_contact_selected=lambda u: None,
            on_add_contact_clicked=lambda: None,
            on_theme_toggle_clicked=lambda: None,
        )

        contact = User("alice", "alice", "Alice Smith", "AS", True)
        sidebar.set_contacts([contact])
        card = sidebar._card_widgets["alice"]

        # Default unselected
        assert card.cget("fg_color") == Theme.BG_SURFACE

        # Mouse enter
        sidebar._on_card_hover_enter("alice")
        assert card.cget("fg_color") == Theme.BG_HOVER

        # Mouse leave
        sidebar._on_card_hover_leave("alice")
        assert card.cget("fg_color") == Theme.BG_SURFACE

        # Select Alice then test hover
        sidebar.select_contact("alice")
        assert card.cget("fg_color") == Theme.BG_SELECTED

        # Mouse enter on selected card should stay BG_SELECTED
        sidebar._on_card_hover_enter("alice")
        assert card.cget("fg_color") == Theme.BG_SELECTED

        # Mouse leave on selected card should stay BG_SELECTED
        sidebar._on_card_hover_leave("alice")
        assert card.cget("fg_color") == Theme.BG_SELECTED
    finally:
        root.destroy()
