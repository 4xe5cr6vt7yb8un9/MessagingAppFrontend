"""Entry point for the NexusChat messaging desktop application."""

from pathlib import Path
import sys

# Ensure src directory is in sys.path when invoked via python -m src.messaging_app.main or directly
_SRC_DIR = str(Path(__file__).resolve().parent.parent)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from messaging_app.cache.database import DatabaseCache
from messaging_app.config import AppConfig
from messaging_app.services.tcp_service import TcpMessagingService
from messaging_app.ui.app import MessagingApp


def main() -> None:
    """Initialize services and launch the primary application loop."""
    if "--help" in sys.argv or "-h" in sys.argv:
        print("NexusChat - Modern Desktop Messaging Application")
        print("\nUsage: python -m src.messaging_app.main [options]")
        print("\nOptions:")
        print("  -h, --help  Show this help message and exit.")
        print("\nConfiguration is loaded from environment variables or .env file.")
        print("Supported environment variables:")
        print("  SERVER_IP            Server IP address (default: 127.0.0.1)")
        print("  SERVER_PORT          Server TCP port (default: 9000)")
        print("  CLIENT_USER_ID       Current user unique ID")
        print("  CLIENT_USERNAME      Current user handle")
        print("  CLIENT_DISPLAY_NAME  Current user display name")
        print("  LOCAL_DB_PATH        Path to SQLite cache database")
        return

    config = AppConfig.from_env()
    db_cache = DatabaseCache(config.local_db_path)
    service = TcpMessagingService(config=config, db_cache=db_cache)
    service.start()

    try:
        app = MessagingApp(service=service)
        app.mainloop()
    finally:
        service.stop()


if __name__ == "__main__":
    main()
