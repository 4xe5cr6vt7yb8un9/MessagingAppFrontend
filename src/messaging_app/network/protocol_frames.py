"""Encoding, decoding, and builders for Newline-Delimited JSON (NDJSON) packets."""

import json
from typing import Any

__all__ = [
    "build_identify",
    "build_query_user",
    "build_send_message",
    "decode_lines",
    "encode_packet",
]


def encode_packet(payload: dict[str, Any]) -> bytes:
    """Serialize dictionary payload to UTF-8 encoded bytes terminated by newline."""
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"


def decode_lines(buffer: bytes) -> tuple[list[dict[str, Any]], bytes]:
    """Parse newline-delimited chunks into JSON dictionaries, returning trailing remainder."""
    packets: list[dict[str, Any]] = []
    lines = buffer.split(b"\n")
    # The last element after split is either empty (if buffer ended in \n) or incomplete
    remainder = lines[-1]

    for line in lines[:-1]:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            parsed = json.loads(stripped.decode("utf-8"))
            if isinstance(parsed, dict):
                packets.append(parsed)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

    return packets, remainder


def build_identify(user_id: str, username: str, display_name: str) -> dict[str, Any]:
    """Build connection handshake packet."""
    return {
        "action": "identify",
        "user_id": user_id,
        "username": username,
        "display_name": display_name,
    }


def build_send_message(message_id: str, receiver_id: str, content: str) -> dict[str, Any]:
    """Build outgoing chat message packet replacing sender_id with receiver_id."""
    return {
        "action": "message",
        "message_id": message_id,
        "receiver_id": receiver_id,
        "content": content,
    }


def build_query_user(query_id: str, username: str) -> dict[str, Any]:
    """Build remote user query request packet."""
    return {
        "action": "query_user",
        "query_id": query_id,
        "username": username,
    }
