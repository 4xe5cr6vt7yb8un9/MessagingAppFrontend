"""Entry point for the NexusChat messaging desktop application."""

from pathlib import Path
import sys

# Ensure src directory is in sys.path when invoked via python -m src.messaging_app.main or directly
_SRC_DIR = str(Path(__file__).resolve().parent.parent)
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from messaging_app.services.dummy_service import DummyMessagingService
from messaging_app.ui.app import MessagingApp


def main() -> None:
    """Initialize services and launch the primary application loop."""
    if "--help" in sys.argv or "-h" in sys.argv:
        print("NexusChat - Modern Desktop Messaging Application")
        print("\nUsage: python -m src.messaging_app.main [options]")
        print("\nOptions:")
        print("  -h, --help  Show this help message and exit.")
        return

    service = DummyMessagingService(simulation_delay=1.2)
    app = MessagingApp(service=service)
    app.mainloop()


if __name__ == "__main__":
    main()

