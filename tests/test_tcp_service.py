"""Integration and unit tests for TcpMessagingService."""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path
import socket
import sys
import threading
import time
from typing import Any
import pytest

# Ensure src is in sys.path for standalone pytest invocations
_SRC_PATH = str(Path(__file__).resolve().parent.parent / "src")
if _SRC_PATH not in sys.path:
    sys.path.insert(0, _SRC_PATH)

from messaging_app.cache.database import DatabaseCache
from messaging_app.config import AppConfig
from messaging_app.models.message import Message
from messaging_app.models.user import User
from messaging_app.network.protocol_frames import decode_lines, encode_packet
from messaging_app.services.protocol import MessagingServiceProtocol
from messaging_app.services.tcp_service import TcpMessagingService


def wait_until(predicate: Callable[[], bool], timeout: float = 2.0, interval: float = 0.05) -> bool:
    """Poll predicate until True or timeout expires."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


@pytest.fixture
def mock_messaging_server():
    """Fixture providing a mock TCP server socket that handles client connections."""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(("127.0.0.1", 0))
    server_sock.listen(5)
    host, port = server_sock.getsockname()
    stop_event = threading.Event()
    received_packets: list[dict[str, Any]] = []
    client_connections: list[socket.socket] = []

    def handle_client(conn: socket.socket) -> None:
        buf = b""
        conn.settimeout(0.2)
        while not stop_event.is_set():
            try:
                data = conn.recv(2048)
                if not data:
                    break
                buf += data
                pkts, buf = decode_lines(buf)
                for p in pkts:
                    received_packets.append(p)
                    # Auto-reply to query_user
                    if p.get("action") == "query_user":
                        u = p.get("username")
                        exists = (u == "bob")
                        resp = {
                            "action": "query_user_response",
                            "query_id": p.get("query_id"),
                            "exists": exists,
                            "user_id": "user_bob" if exists else "",
                            "username": "bob" if exists else u,
                            "display_name": "Bob Martinez" if exists else "",
                            "is_online": True,
                        }
                        conn.sendall(encode_packet(resp))
            except socket.timeout:
                continue
            except Exception:
                break

    def run_server() -> None:
        server_sock.settimeout(0.2)
        while not stop_event.is_set():
            try:
                conn, _ = server_sock.accept()
                client_connections.append(conn)
                t = threading.Thread(target=handle_client, args=(conn,), daemon=True)
                t.start()
            except socket.timeout:
                continue

    t_srv = threading.Thread(target=run_server, daemon=True)
    t_srv.start()
    yield host, port, received_packets, client_connections
    stop_event.set()
    t_srv.join(timeout=1.0)
    for c in client_connections:
        try:
            c.close()
        except Exception:
            pass
    server_sock.close()


def test_service_protocol_and_lifecycle(tmp_path: Path, mock_messaging_server) -> None:
    """Verify service protocol compliance, identify handshake, message send, and query user."""
    host, port, server_pkts, _ = mock_messaging_server
    config = AppConfig(
        server_ip=host,
        server_port=port,
        client_user_id="user_alice",
        client_username="alice",
        client_display_name="Alice Smith",
        local_db_path=tmp_path / "cache.db",
    )
    db = DatabaseCache(config.local_db_path)
    service = TcpMessagingService(config, db)
    assert isinstance(service, MessagingServiceProtocol)

    service.start()
    # Wait until identify handshake is received
    assert wait_until(lambda: any(p.get("action") == "identify" and p.get("username") == "alice" for p in server_pkts))

    # Test send message
    sent_msg = service.send_message("user_bob", "Hello Bob over TCP!")
    assert sent_msg.content == "Hello Bob over TCP!"
    assert sent_msg.is_outgoing is True

    # Poll until outgoing packet replaced sender_id with receiver_id
    assert wait_until(lambda: any(p.get("action") == "message" for p in server_pkts))
    msg_pkts = [p for p in server_pkts if p.get("action") == "message"]
    assert len(msg_pkts) >= 1
    assert msg_pkts[0]["receiver_id"] == "user_bob"
    assert "sender_id" not in msg_pkts[0]

    # Verify message is cached locally in sqlite
    cached_msgs = service.get_messages("user_bob")
    assert len(cached_msgs) == 1
    assert cached_msgs[0].content == "Hello Bob over TCP!"

    # Test query user exists
    user_bob = service.query_user("bob")
    assert user_bob is not None
    assert user_bob.username == "bob"
    assert user_bob.display_name == "Bob Martinez"
    assert user_bob.avatar_initials == "BM"
    assert user_bob.is_online is True

    # Test query user not exists
    user_unknown = service.query_user("unknown_user")
    assert user_unknown is None

    service.stop()


def test_add_contact_flow(tmp_path: Path, mock_messaging_server) -> None:
    """Verify add_contact queries server, saves to cache, and fires callback."""
    host, port, _, _ = mock_messaging_server
    config = AppConfig(
        server_ip=host,
        server_port=port,
        client_user_id="user_alice",
        client_username="alice",
        client_display_name="Alice Smith",
        local_db_path=tmp_path / "cache.db",
    )
    db = DatabaseCache(config.local_db_path)
    service = TcpMessagingService(config, db)
    service.start()
    assert wait_until(lambda: service._client.is_connected())

    added_contacts: list[User] = []
    service.subscribe_contact_added(lambda u: added_contacts.append(u))

    # Add existing remote user with custom display name
    contact = service.add_contact("@bob", "Bobby M.")
    assert contact.id == "user_bob"
    assert contact.username == "bob"
    assert contact.display_name == "Bobby M."
    assert contact.avatar_initials == "BM"
    assert len(added_contacts) == 1
    assert added_contacts[0].username == "bob"

    # Verify contact is persisted in db
    contacts_in_db = service.get_contacts()
    assert any(c.username == "bob" for c in contacts_in_db)

    # Empty username raises ValueError
    with pytest.raises(ValueError, match="cannot be empty"):
        service.add_contact("   ", "Empty")

    # Non-existent user raises ValueError
    with pytest.raises(ValueError, match="does not exist on server"):
        service.add_contact("nonexistent_guy", "No Guy")

    service.stop()

    # Disconnected state raises ConnectionError
    with pytest.raises(ConnectionError, match="not connected"):
        service.add_contact("bob", "Bob")


def test_incoming_message_and_callbacks(tmp_path: Path, mock_messaging_server) -> None:
    """Verify incoming chat message packets are saved to DB and delivered to callbacks."""
    host, port, _, server_conns = mock_messaging_server
    config = AppConfig(
        server_ip=host,
        server_port=port,
        client_user_id="user_alice",
        client_username="alice",
        client_display_name="Alice Smith",
        local_db_path=tmp_path / "cache.db",
    )
    db = DatabaseCache(config.local_db_path)
    service = TcpMessagingService(config, db)

    received_messages: list[Message] = []
    service.subscribe_message_received(lambda m: received_messages.append(m))

    service.start()
    assert wait_until(lambda: len(server_conns) > 0 and service._client.is_connected())
    conn = server_conns[0]

    # Server pushes an incoming message
    incoming_pkt = {
        "action": "message",
        "message_id": "msg_inc_1",
        "sender_id": "user_bob",
        "receiver_id": "user_alice",
        "content": "Hey Alice! How are you?",
        "timestamp": datetime.now().isoformat(),
    }
    conn.sendall(encode_packet(incoming_pkt))

    assert wait_until(lambda: len(received_messages) == 1)
    msg = received_messages[0]
    assert msg.id == "msg_inc_1"
    assert msg.sender_id == "user_bob"
    assert msg.content == "Hey Alice! How are you?"
    assert msg.is_outgoing is False

    # Check database cache
    cached = service.get_messages("user_bob")
    assert any(m.id == "msg_inc_1" for m in cached)

    service.stop()


def test_history_sync_packet(tmp_path: Path, mock_messaging_server) -> None:
    """Verify history_sync packets merge historical messages into local SQLite cache."""
    host, port, _, server_conns = mock_messaging_server
    config = AppConfig(
        server_ip=host,
        server_port=port,
        client_user_id="user_alice",
        client_username="alice",
        client_display_name="Alice Smith",
        local_db_path=tmp_path / "cache.db",
    )
    db = DatabaseCache(config.local_db_path)
    service = TcpMessagingService(config, db)
    service.start()
    assert wait_until(lambda: len(server_conns) > 0 and service._client.is_connected())

    conn = server_conns[0]
    sync_pkt = {
        "action": "history_sync",
        "messages": [
            "malformed_non_dict_entry",  # Guard verification
            {
                "message_id": "hist_1",
                "sender_id": "user_bob",
                "receiver_id": "user_alice",
                "content": "Old message 1",
                "timestamp": "2026-11-20T10:00:00",
            },
            {
                "message_id": "hist_2",
                "sender_id": "user_alice",
                "receiver_id": "user_bob",
                "content": "Old message 2",
                "timestamp": "2026-11-20T10:01:00",
            },
        ],
    }
    conn.sendall(encode_packet(sync_pkt))
    assert wait_until(lambda: len(service.get_messages("user_bob")) == 2)

    messages = service.get_messages("user_bob")
    assert len(messages) == 2
    assert messages[0].content == "Old message 1"
    assert messages[0].is_outgoing is False
    assert messages[1].content == "Old message 2"
    assert messages[1].is_outgoing is True

    service.stop()


def test_presence_and_connection_status_subscriptions(tmp_path: Path, mock_messaging_server) -> None:
    """Verify presence update and connection status events trigger callbacks."""
    host, port, _, server_conns = mock_messaging_server
    config = AppConfig(
        server_ip=host,
        server_port=port,
        client_user_id="user_alice",
        client_username="alice",
        client_display_name="Alice Smith",
        local_db_path=tmp_path / "cache.db",
    )
    db = DatabaseCache(config.local_db_path)
    # Pre-populate contact in db
    db.upsert_contact(User("user_bob", "bob", "Bob Martinez", "BM", is_online=False))

    service = TcpMessagingService(config, db)

    presence_updates: list[tuple[str, bool]] = []
    status_updates: list[tuple[str, str]] = []

    service.subscribe_presence_updated(lambda uid, online: presence_updates.append((uid, online)))
    service.subscribe_connection_status(lambda st, det: status_updates.append((st, det)))

    service.start()
    assert wait_until(lambda: len(server_conns) > 0 and any(st == "CONNECTED" for st, _ in status_updates))

    conn = server_conns[0]
    status_pkt = {
        "action": "user_status",
        "user_id": "user_bob",
        "is_online": True,
    }
    conn.sendall(encode_packet(status_pkt))
    assert wait_until(lambda: any(uid == "user_bob" and online is True for uid, online in presence_updates))

    contacts = service.get_contacts()
    bob = next(c for c in contacts if c.id == "user_bob")
    assert bob.is_online is True

    service.stop()


def test_send_message_validation(tmp_path: Path) -> None:
    """Verify send_message raises on empty content."""
    config = AppConfig(
        server_ip="127.0.0.1",
        server_port=9999,
        client_user_id="user_alice",
        client_username="alice",
        client_display_name="Alice",
        local_db_path=tmp_path / "cache.db",
    )
    db = DatabaseCache(config.local_db_path)
    service = TcpMessagingService(config, db)

    with pytest.raises(ValueError, match="cannot be empty"):
        service.send_message("user_bob", "   ")


def test_query_user_fast_fail_disconnected(tmp_path: Path) -> None:
    """Verify query_user fast-fails returning None immediately when disconnected or timeout<=0."""
    config = AppConfig(
        server_ip="127.0.0.1",
        server_port=9999,
        client_user_id="user_alice",
        client_username="alice",
        client_display_name="Alice",
        local_db_path=tmp_path / "cache.db",
    )
    db = DatabaseCache(config.local_db_path)
    service = TcpMessagingService(config, db)
    # Not started -> disconnected
    start_time = time.time()
    result = service.query_user("bob", timeout=5.0)
    elapsed = time.time() - start_time
    assert result is None
    assert elapsed < 0.1  # Fast-failed immediately!

    # timeout <= 0
    assert service.query_user("bob", timeout=0) is None
    assert service.query_user("bob", timeout=-1.0) is None
