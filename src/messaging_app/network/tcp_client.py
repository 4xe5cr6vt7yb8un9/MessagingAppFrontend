"""Persistent TCP client socket engine with auto-reconnection and thread-safe queue."""

import queue
import select
import socket
import threading
from typing import Any, Callable

from messaging_app.network.protocol_frames import decode_lines, encode_packet


class TcpClient:
    """Manages continuous TCP connection with a remote server in a background thread."""

    def __init__(
        self,
        host: str,
        port: int,
        on_packet: Callable[[dict[str, Any]], None],
        on_status: Callable[[str, str], None],
        reconnect_interval: float = 2.0,
    ) -> None:
        self.host = host
        self.port = port
        self.on_packet = on_packet
        self.on_status = on_status
        self.reconnect_interval = reconnect_interval

        self._send_queue: queue.Queue[dict[str, Any]] = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._connected = False
        self._sock: socket.socket | None = None
        self._lock = threading.Lock()

    def is_connected(self) -> bool:
        """Return True if socket is currently active and connected."""
        with self._lock:
            return self._connected

    def start(self) -> None:
        """Start persistent background connection loop thread."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._run_loop,
                daemon=True,
                name="TcpClientThread",
            )
            self._thread.start()

    def stop(self) -> None:
        """Signal background thread to stop, close socket, and wait for thread exit."""
        self._stop_event.set()
        with self._lock:
            sock = self._sock
            self._sock = None
            if sock:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    sock.close()
                except Exception:
                    pass
            self._connected = False

        if self._thread and self._thread.is_alive():
            if threading.current_thread() != self._thread:
                self._thread.join(timeout=2.0)

    def send_packet(self, packet: dict[str, Any]) -> None:
        """Enqueue packet for transmission over the socket."""
        self._send_queue.put(packet)

    def _set_status(self, status: str, detail: str = "") -> None:
        """Invoke on_status callback safely without raising exceptions."""
        try:
            self.on_status(status, detail)
        except Exception:
            pass

    def _run_loop(self) -> None:
        """Background connection supervisor handling reconnect backoff."""
        backoff = self.reconnect_interval

        while not self._stop_event.is_set():
            self._set_status("CONNECTING", f"{self.host}:{self.port}")
            sock: socket.socket | None = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                with self._lock:
                    if self._stop_event.is_set():
                        sock.close()
                        break
                    self._sock = sock

                sock.settimeout(4.0)
                sock.connect((self.host, self.port))
                if self._stop_event.is_set():
                    with self._lock:
                        self._sock = None
                    sock.close()
                    break

                sock.setblocking(False)
                with self._lock:
                    self._connected = True
                backoff = self.reconnect_interval
                self._set_status("CONNECTED", f"{self.host}:{self.port}")

                self._handle_socket_session(sock)
            except (socket.error, OSError) as exc:
                with self._lock:
                    self._connected = False
                    self._sock = None
                if sock is not None:
                    try:
                        sock.close()
                    except Exception:
                        pass
                if not self._stop_event.is_set():
                    self._set_status("RECONNECTING", str(exc))
                    self._stop_event.wait(backoff)
                    backoff = min(backoff * 1.5, 10.0)
            else:
                with self._lock:
                    self._connected = False
                    self._sock = None
                if sock is not None:
                    try:
                        sock.close()
                    except Exception:
                        pass
                if not self._stop_event.is_set():
                    self._set_status("RECONNECTING", "Connection closed by remote host")
                    self._stop_event.wait(backoff)
                    backoff = min(backoff * 1.5, 10.0)

        with self._lock:
            self._connected = False
            self._sock = None
        self._set_status("DISCONNECTED", "Client stopped")

    def _handle_socket_session(self, sock: socket.socket) -> None:
        """Run I/O select loop for an established socket connection."""
        buffer = b""

        while not self._stop_event.is_set() and self._connected:
            read_socks = [sock]
            write_socks = [sock] if not self._send_queue.empty() else []

            try:
                r_ready, w_ready, x_ready = select.select(read_socks, write_socks, read_socks, 0.2)
            except (select.error, OSError, ValueError):
                break

            if x_ready:
                break

            # Process outgoing packets
            if w_ready:
                while not self._send_queue.empty():
                    try:
                        packet = self._send_queue.get_nowait()
                    except queue.Empty:
                        break

                    try:
                        data = encode_packet(packet)
                    except (TypeError, ValueError, Exception):
                        # Discard un-serializable payload safely without crashing worker thread
                        continue

                    try:
                        sock.sendall(data)
                    except BlockingIOError:
                        self._send_queue.put(packet)
                        break
                    except (socket.error, OSError):
                        return

            # Process incoming data
            if r_ready:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        # Server closed connection (EOF)
                        break
                    buffer += chunk
                    packets, buffer = decode_lines(buffer)
                    for pkt in packets:
                        try:
                            self.on_packet(pkt)
                        except Exception:
                            pass
                except BlockingIOError:
                    pass
                except (socket.error, OSError):
                    break
