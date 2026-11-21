"""Networking package for persistent TCP communication."""

from messaging_app.network.protocol_frames import (
    build_identify,
    build_query_user,
    build_send_message,
    decode_lines,
    encode_packet,
)
from messaging_app.network.tcp_client import TcpClient

__all__ = [
    "TcpClient",
    "build_identify",
    "build_query_user",
    "build_send_message",
    "decode_lines",
    "encode_packet",
]
