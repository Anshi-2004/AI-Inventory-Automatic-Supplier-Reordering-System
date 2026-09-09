"""
Abstract email service base class.
Concrete implementations: GmailService, (future: ResendService, SendGridService).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class EmailMessage:
    recipient: str
    subject: str
    body: str
    reply_to: str | None = None


class EmailService(ABC):
    """Abstract email service. Implement this to add new email providers."""

    @abstractmethod
    async def send_email(self, message: EmailMessage) -> bool:
        """
        Send an email. Returns True on success, raises on failure.
        Never silently fail — always log and raise on error.
        """
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Returns True if all required credentials are present."""
        ...
