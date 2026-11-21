from datetime import datetime
from pathlib import Path
import pytest
from messaging_app.cache.database import DatabaseCache
from messaging_app.models.message import Message
from messaging_app.models.user import User


@pytest.fixture
def db_cache(tmp_path: Path) -> DatabaseCache:
    db_file = tmp_path / "test_chat.db"
    return DatabaseCache(db_file)


def test_save_and_get_messages(db_cache: DatabaseCache) -> None:
    msg1 = Message("m1", "alice", "me", "Hello!", datetime(2026, 11, 21, 10, 0), False)
    msg2 = Message("m2", "me", "alice", "Hi Alice!", datetime(2026, 11, 21, 10, 1), True)

    db_cache.save_message(msg1)
    db_cache.save_message(msg2)

    alice_history = db_cache.get_messages("alice")
    assert len(alice_history) == 2
    assert alice_history[0].id == "m1"
    assert alice_history[0].is_outgoing is False
    assert alice_history[1].id == "m2"
    assert alice_history[1].is_outgoing is True


def test_merge_history_deduplication(db_cache: DatabaseCache) -> None:
    existing = Message("m1", "bob", "me", "First message", datetime(2026, 11, 20, 12, 0), False)
    db_cache.save_message(existing)

    server_sync = [
        Message("m1", "bob", "me", "First message", datetime(2026, 11, 20, 12, 0), False),
        Message("m2", "bob", "me", "Second message", datetime(2026, 11, 20, 12, 5), False),
    ]

    new_count, dup_count = db_cache.merge_history(server_sync)
    assert new_count == 1
    assert dup_count == 1

    bob_history = db_cache.get_messages("bob")
    assert len(bob_history) == 2


def test_upsert_and_get_contacts(db_cache: DatabaseCache) -> None:
    alice = User("alice", "alice", "Alice Smith", "AS", True)
    db_cache.upsert_contact(alice)

    contacts = db_cache.get_contacts()
    assert len(contacts) == 1
    assert contacts[0].username == "alice"
    assert contacts[0].is_online is True

    # Update online status
    db_cache.update_contact_status("alice", False)
    updated = db_cache.get_contacts()
    assert updated[0].is_online is False


def test_contact_ordering(db_cache: DatabaseCache) -> None:
    user_offline_a = User("u1", "charlie", "Charlie Brown", "CB", False)
    user_online_b = User("u2", "bob", "Bob Ross", "BR", True)
    user_online_a = User("u3", "alice", "Alice Wonder", "AW", True)

    db_cache.upsert_contact(user_offline_a)
    db_cache.upsert_contact(user_online_b)
    db_cache.upsert_contact(user_online_a)

    contacts = db_cache.get_contacts()
    assert len(contacts) == 3
    # Online contacts first, then sorted by display_name ASC
    assert [c.id for c in contacts] == ["u3", "u2", "u1"]


def test_db_path_creates_nested_directory(tmp_path: Path) -> None:
    nested_path = tmp_path / "nested" / "sub" / "chat.db"
    cache = DatabaseCache(str(nested_path))
    assert nested_path.exists()
    assert cache.get_contacts() == []


def test_contact_upsert_updates_fields(db_cache: DatabaseCache) -> None:
    initial = User("u1", "alice", "Alice Old", "AO", False)
    db_cache.upsert_contact(initial)

    updated = User("u1", "alice_new", "Alice New", "AN", True)
    db_cache.upsert_contact(updated)

    contacts = db_cache.get_contacts()
    assert len(contacts) == 1
    assert contacts[0].id == "u1"
    assert contacts[0].username == "alice_new"
    assert contacts[0].display_name == "Alice New"
    assert contacts[0].avatar_initials == "AN"
    assert contacts[0].is_online is True


def test_get_messages_empty_or_nonexistent_contact(db_cache: DatabaseCache) -> None:
    messages = db_cache.get_messages("nonexistent")
    assert messages == []


def test_invalid_timestamp_fallback(db_cache: DatabaseCache) -> None:
    with db_cache._lock, db_cache._get_connection() as conn:
        conn.execute(
            """
            INSERT INTO messages (id, sender_id, recipient_id, content, timestamp, is_outgoing)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("m_corrupt", "alice", "me", "Invalid timestamp test", "not-a-timestamp", 0),
        )

    messages = db_cache.get_messages("alice")
    assert len(messages) == 1
    assert messages[0].id == "m_corrupt"
    assert isinstance(messages[0].timestamp, datetime)


def test_schema_indexes_exist(db_cache: DatabaseCache) -> None:
    with db_cache._lock, db_cache._get_connection() as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='messages'"
        )
        indexes = {row["name"] for row in cursor.fetchall()}

    assert "idx_messages_pair" in indexes
    assert "idx_messages_recipient_ts" in indexes


def test_connection_closes_deterministically(tmp_path: Path) -> None:
    db_file = tmp_path / "lock_test.db"
    cache = DatabaseCache(db_file)
    msg = Message("m1", "alice", "me", "hi", datetime.now(), False)
    cache.save_message(msg)

    # If connection was not closed, attempting to open in exclusive mode or unlink can fail on Windows
    db_file.unlink()
    assert not db_file.exists()


