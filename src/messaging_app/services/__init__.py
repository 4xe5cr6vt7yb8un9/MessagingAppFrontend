"""Services package exports."""

from messaging_app.services.dummy_service import DummyMessagingService
from messaging_app.services.protocol import MessagingServiceProtocol

__all__ = ["MessagingServiceProtocol", "DummyMessagingService"]
