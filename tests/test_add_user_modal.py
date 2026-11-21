"""Unit tests for AddUserModal component."""

from pathlib import Path
import sys
from unittest.mock import MagicMock

import customtkinter
import pytest

# Ensure src is in sys.path for standalone pytest invocations
_SRC_PATH = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_PATH not in sys.path:
    sys.path.insert(0, _SRC_PATH)

from messaging_app.ui.components import AddUserModal
from messaging_app.ui.components.add_user_modal import AddUserModal as DirectAddUserModal
from messaging_app.ui.theme import Theme


@pytest.fixture(scope="module")
def root():
    """Shared CTk root window for modal tests to avoid repeated Tk interpreter cycles."""
    r = customtkinter.CTk()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


def test_components_package_exports() -> None:
    """Verify that components __init__ exposes AddUserModal."""
    assert AddUserModal is DirectAddUserModal


def test_add_user_modal_creation(root) -> None:
    """Verify modal creation, title, and setting errors."""
    submitted: list[tuple[str, str]] = []
    modal = AddUserModal(root, on_submit=lambda u, d: submitted.append((u, d)))
    try:
        assert modal.title() == "Add New Contact"
        assert modal.winfo_exists()

        # Test error setting
        modal.set_error("Username is required")
        assert modal.error_label.cget("text") == "Username is required"
    finally:
        if modal.winfo_exists():
            modal.destroy()


def test_add_user_modal_validation_empty_username(root) -> None:
    """Verify empty or whitespace-only username fails validation."""
    on_submit_mock = MagicMock()
    modal = AddUserModal(root, on_submit=on_submit_mock)
    try:
        # Trigger submit with empty username
        modal._handle_submit()
        assert on_submit_mock.call_count == 0
        assert "Username is required" in modal.error_label.cget("text")

        # Whitespace-only username
        modal.username_entry.insert(0, "   ")
        modal._handle_submit()
        assert on_submit_mock.call_count == 0
        assert "Username is required" in modal.error_label.cget("text")
    finally:
        if modal.winfo_exists():
            modal.destroy()


def test_add_user_modal_successful_submit(root) -> None:
    """Verify valid username and display name submission with whitespace stripping."""
    submitted: list[tuple[str, str]] = []
    modal = AddUserModal(root, on_submit=lambda u, d: submitted.append((u, d)))
    try:
        modal.username_entry.delete(0, "end")
        modal.username_entry.insert(0, "  sarah_c  ")
        modal.name_entry.delete(0, "end")
        modal.name_entry.insert(0, "  Sarah Connor  ")

        modal.submit_btn.invoke()

        assert len(submitted) == 1
        assert submitted[0] == ("sarah_c", "Sarah Connor")
    finally:
        if modal.winfo_exists():
            modal.destroy()


def test_add_user_modal_return_key_and_escape(root) -> None:
    """Verify Return key triggers submit and Escape destroys modal."""
    submitted: list[tuple[str, str]] = []
    modal = AddUserModal(root, on_submit=lambda u, d: submitted.append((u, d)))
    try:
        modal.username_entry.insert(0, "john_doe")
        modal._handle_return(None)
        assert len(submitted) == 1
        assert submitted[0] == ("john_doe", "")

        # Verify Escape key binding destroys dialog
        modal._handle_escape(None)
        assert not modal.winfo_exists()
    finally:
        if modal.winfo_exists():
            modal.destroy()


def test_add_user_modal_cancel_button(root) -> None:
    """Verify cancel button destroys modal."""
    modal = AddUserModal(root, on_submit=lambda u, d: None)
    try:
        assert modal.winfo_exists()
        modal.cancel_btn.invoke()
        assert not modal.winfo_exists()
    finally:
        if modal.winfo_exists():
            modal.destroy()
