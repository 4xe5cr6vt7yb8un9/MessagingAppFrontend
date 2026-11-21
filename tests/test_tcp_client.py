"""Tests for persistent TcpClient socket engine."""

import socket
import threading
import time
from typing import Any
import pytest

from messaging_app.network.protocol_frames import decode_lines, encode_packet
from messaging_app.network.tcp_client import TcpClient


@pytest.fixture
def mock_server():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(("127.0.0.1", 0))
    server_sock.listen(5)
    host, port = server_sock.getsockname()
    stop_event = threading.Event()
    clients: list[socket.socket] = []

    def run_server():
        server_sock.settimeout(0.2)
        while not stop_event.is_set():
            try:
                conn, _ = server_sock.accept()
                clients.append(conn)
            except socket.timeout:
                continue
            except OSError:
                break

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    yield host, port, clients
    stop_event.set()
    thread.join(timeout=1.0)
    for c in clients:
        try:
            c.close()
        except Exception:
            pass
    try:
        server_sock.close()
    except Exception:
        pass


def test_tcp_client_connect_and_exchange(mock_server):
    host, port, clients = mock_server
    received_packets: list[dict[str, Any]] = []
    statuses: list[str] = []

    client = TcpClient(
        host=host,
        port=port,
        on_packet=lambda p: received_packets.append(p),
        on_status=lambda s, d: statuses.append(s),
        reconnect_interval=0.1,
    )
    client.start()

    # Wait for connection
    time.sleep(0.3)
    assert client.is_connected() is True
    assert "CONNECTED" in statuses
    assert len(clients) >= 1

    # Send from server to client
    server_conn = clients[0]
    server_conn.sendall(encode_packet({"action": "welcome", "text": "hello"}))
    time.sleep(0.2)
    assert len(received_packets) >= 1
    assert received_packets[0]["action"] == "welcome"

    # Send from client to server
    client.send_packet({"action": "ping", "client_time": 12345})
    time.sleep(0.2)

    # Server receives outgoing packet
    server_conn.settimeout(0.5)
    raw_data = server_conn.recv(4096)
    server_pkts, _ = decode_lines(raw_data)
    assert len(server_pkts) >= 1
    assert server_pkts[0]["action"] == "ping"
    assert server_pkts[0]["client_time"] == 12345

    client.stop()
    time.sleep(0.2)
    assert client.is_connected() is False


def test_tcp_client_reconnect(mock_server):
    host, port, clients = mock_server
    received_packets: list[dict[str, Any]] = []
    statuses: list[str] = []

    client = TcpClient(
        host=host,
        port=port,
        on_packet=lambda p: received_packets.append(p),
        on_status=lambda s, d: statuses.append(s),
        reconnect_interval=0.1,
    )
    client.start()
    time.sleep(0.3)
    assert client.is_connected() is True
    assert len(clients) >= 1

    # Drop the first client connection from server side
    clients[0].close()
    time.sleep(0.3)

    # Client should attempt reconnect and connect again
    time.sleep(0.4)
    assert "RECONNECTING" in statuses
    assert client.is_connected() is True
    assert len(clients) >= 2

    client.stop()


def test_tcp_client_stop_when_unreachable():
    # Port 1 is typically not listening
    statuses: list[str] = []
    client = TcpClient(
        host="127.0.0.1",
        port=59999,
        on_packet=lambda p: None,
        on_status=lambda s, d: statuses.append(s),
        reconnect_interval=0.1,
    )
    client.start()
    time.sleep(0.2)
    assert client.is_connected() is False
    assert "CONNECTING" in statuses

    # Stop should return promptly without waiting on a long sleep
    start_time = time.time()
    client.stop()
    duration = time.time() - start_time
    assert duration < 1.0
    assert "DISCONNECTED" in statuses


def test_tcp_client_idempotent_lifecycle(mock_server):
    host, port, _ = mock_server
    client = TcpClient(
        host=host,
        port=port,
        on_packet=lambda p: None,
        on_status=lambda s, d: None,
        reconnect_interval=0.1,
    )
    # Multiple starts should not create multiple threads
    client.start()
    client.start()
    time.sleep(0.2)
    assert client.is_connected() is True

    # Multiple stops should be safe
    client.stop()
    client.stop()
    assert client.is_connected() is False


def test_tcp_client_error_resilience(mock_server):
    host, port, clients = mock_server
    received: list[dict[str, Any]] = []

    def faulty_callback(pkt: dict[str, Any]) -> None:
        if pkt.get("action") == "explode":
            raise RuntimeError("Boom!")
        received.append(pkt)

    client = TcpClient(
        host=host,
        port=port,
        on_packet=faulty_callback,
        on_status=lambda s, d: None,
        reconnect_interval=0.1,
    )
    client.start()
    time.sleep(0.2)

    server_conn = clients[0]
    # Send malformed data and explosive packet, followed by valid packet
    server_conn.sendall(b"not-valid-json\n")
    server_conn.sendall(encode_packet({"action": "explode"}))
    server_conn.sendall(encode_packet({"action": "survived"}))
    time.sleep(0.3)

    assert len(received) == 1
    assert received[0]["action"] == "survived"

    client.stop()
