"""Tests for email service with mocked Gmail API."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.email.email_service import EmailMessage
from app.email.gmail_service import GmailService


@pytest.mark.asyncio
async def test_gmail_send_success():
    """Gmail service sends email and returns True."""
    service = GmailService()
    mock_gmail_build = MagicMock()
    mock_gmail_build.users().messages().send().execute.return_value = {"id": "msg123"}

    with patch.object(service, "_get_gmail_service", return_value=mock_gmail_build):
        result = await service.send_email(EmailMessage(
            recipient="supplier@test.com",
            subject="Test Subject",
            body="Test Body",
        ))
    assert result is True


@pytest.mark.asyncio
async def test_gmail_send_failure():
    """Gmail service raises RuntimeError on send failure."""
    service = GmailService()

    with patch.object(service, "_get_gmail_service", side_effect=Exception("Auth failed")):
        with pytest.raises(RuntimeError):
            await service.send_email(EmailMessage(
                recipient="bad@test.com",
                subject="Test",
                body="Test",
            ))


def test_gmail_not_configured_without_token():
    """is_configured returns False when token file doesn't exist."""
    service = GmailService()
    with patch("os.path.exists", return_value=False):
        assert service.is_configured() is False
