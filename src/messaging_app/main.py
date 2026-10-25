"""Entry point for the NexusChat messaging desktop application."""

from messaging_app.services.dummy_service import DummyMessagingService
from messaging_app.ui.app import MessagingApp


def main() -> None:
    """Initialize services and launch the primary application loop."""
    service = DummyMessagingService(simulation_delay=1.2)
    app = MessagingApp(service=service)
    app.mainloop()


if __name__ == "__main__":
    main()
