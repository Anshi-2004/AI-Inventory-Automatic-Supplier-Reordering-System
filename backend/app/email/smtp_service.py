"""
SMTP email service implementation.

Replaces the former GmailService (OAuth2) with a standard SMTP transport.
Uses Python's built-in smtplib — no additional packages required.

Configuration (via .env):
    SMTP_HOST      — SMTP server hostname  (e.g. smtp.gmail.com)
    SMTP_PORT      — SMTP server port      (587 for STARTTLS, 465 for SSL)
    SMTP_USERNAME  — Login username / email address
    SMTP_PASSWORD  — App password (never a plain account password)
    SMTP_USE_TLS   — "true" to use STARTTLS (recommended)
    EMAIL_FROM     — Sender address shown in the From header

For Gmail, SMTP_PASSWORD must be a 16-character App Password generated at:
    Google Account → Security → 2-Step Verification → App passwords
Never store your normal Gmail account password here.

Falls back gracefully: is_configured() returns False when credentials are
missing so callers can surface a helpful error rather than crash.
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.config.settings import settings
from app.email.email_service import EmailMessage, EmailService

logger = logging.getLogger(__name__)


class SmtpEmailService(EmailService):
    """Concrete EmailService that sends via SMTP (STARTTLS or plain TLS)."""

    def is_configured(self) -> bool:
        """Return True only when every required SMTP credential is present."""
        return bool(
            settings.smtp_host
            and settings.smtp_port
            and settings.smtp_username
            and settings.smtp_password
            and settings.email_from
        )

    async def send_email(self, message: EmailMessage) -> bool:
        """
        Send an email via SMTP.

        Returns True on success.
        Raises RuntimeError (wrapping the underlying SMTP exception) on failure
        so the existing error-handling in email_logs.py continues to work.
        """
        if not self.is_configured():
            raise RuntimeError(
                "SMTP is not configured. Set SMTP_HOST, SMTP_PORT, "
                "SMTP_USERNAME, SMTP_PASSWORD, and EMAIL_FROM in your .env file."
            )

        mime_msg = MIMEMultipart("alternative")
        mime_msg["Subject"] = message.subject
        mime_msg["From"] = settings.email_from
        mime_msg["To"] = message.recipient
        if message.reply_to:
            mime_msg["Reply-To"] = message.reply_to

        # Plain-text body (HTML support can be added as a second MIMEText part)
        mime_msg.attach(MIMEText(message.body, "plain"))

        host = settings.smtp_host
        port = settings.smtp_port
        username = settings.smtp_username
        # Password deliberately kept out of any log statement
        password = settings.smtp_password
        use_tls = settings.smtp_use_tls

        try:
            if use_tls:
                # STARTTLS on port 587 (recommended for Gmail and most providers)
                with smtplib.SMTP(host, port, timeout=30) as server:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                    server.login(username, password)
                    server.sendmail(
                        settings.email_from,
                        [message.recipient],
                        mime_msg.as_bytes(),
                    )
            else:
                # SSL on port 465
                with smtplib.SMTP_SSL(host, port, timeout=30) as server:
                    server.ehlo()
                    server.login(username, password)
                    server.sendmail(
                        settings.email_from,
                        [message.recipient],
                        mime_msg.as_bytes(),
                    )

            logger.info(
                "Email sent via SMTP. Recipient: %s, Subject: %s",
                message.recipient,
                message.subject,
            )
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error(
                "SMTP authentication failed for user '%s'. "
                "Check SMTP_USERNAME and SMTP_PASSWORD (use an App Password for Gmail).",
                username,
            )
            raise RuntimeError(
                "SMTP authentication failed. Verify your SMTP_USERNAME and SMTP_PASSWORD."
            )
        except smtplib.SMTPRecipientsRefused as exc:
            logger.error("SMTP recipient refused for %s: %s", message.recipient, exc)
            raise RuntimeError(f"SMTP recipient refused: {message.recipient}") from exc
        except smtplib.SMTPException as exc:
            logger.error(
                "SMTP error sending to %s: %s", message.recipient, exc, exc_info=True
            )
            raise RuntimeError(f"SMTP send failed: {str(exc)}") from exc
        except OSError as exc:
            logger.error(
                "Network error connecting to SMTP server %s:%s — %s",
                host, port, exc, exc_info=True,
            )
            raise RuntimeError(
                f"Could not connect to SMTP server {host}:{port}: {str(exc)}"
            ) from exc


# ── Singleton ─────────────────────────────────────────────────────────────────
_smtp_service: Optional[SmtpEmailService] = None


def get_smtp_service() -> SmtpEmailService:
    """Return the application-wide SmtpEmailService singleton."""
    global _smtp_service
    if _smtp_service is None:
        _smtp_service = SmtpEmailService()
    return _smtp_service
