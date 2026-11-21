"""Unit tests for wire protocol framing, serialization, and packet builders."""

import json
import pytest

from messaging_app.network.protocol_frames import (
    build_identify,
    build_query_user,
    build_send_message,
    decode_lines,
    encode_packet,
)


def test_encode_packet() -> None:
    data = {"action": "identify", "user_id": "u1"}
    encoded = encode_packet(data)
    assert encoded.endswith(b"\n")
    decoded = json.loads(encoded.decode("utf-8").strip())
    assert decoded["action"] == "identify"
    assert decoded["user_id"] == "u1"


def test_decode_lines_complete_and_partial() -> None:
    chunk1 = b'{"action": "ping"}\n{"action": "message", "content": "hi"}\n{"action": "part'
    packets, remaining = decode_lines(chunk1)
    assert len(packets) == 2
    assert packets[0]["action"] == "ping"
    assert packets[1]["content"] == "hi"
    assert remaining == b'{"action": "part'

    chunk2 = remaining + b'ial_done"}\n'
    packets2, remaining2 = decode_lines(chunk2)
    assert len(packets2) == 1
    assert packets2[0]["action"] == "partial_done"
    assert remaining2 == b""


def test_build_send_message_uses_receiver_id() -> None:
    packet = build_send_message(message_id="m123", receiver_id="user_bob", content="Hello!")
    assert packet["action"] == "message"
    assert packet["message_id"] == "m123"
    assert packet["receiver_id"] == "user_bob"
    assert "sender_id" not in packet
    assert packet["content"] == "Hello!"


def test_build_identify_and_query() -> None:
    ident = build_identify("u1", "alice", "Alice Smith")
    assert ident["action"] == "identify"
    assert ident["username"] == "alice"
    assert ident["display_name"] == "Alice Smith"

    qry = build_query_user("q1", "bob")
    assert qry["action"] == "query_user"
    assert qry["query_id"] == "q1"
    assert qry["username"] == "bob"


def test_decode_lines_ignores_malformed_and_blank_lines() -> None:
    buffer = b'\n{"action": "valid"}\n   \nnot-valid-json\n{"action": "valid2"}\n'
    packets, remaining = decode_lines(buffer)
    assert len(packets) == 2
    assert packets[0]["action"] == "valid"
    assert packets[1]["action"] == "valid2"
    assert remaining == b""
