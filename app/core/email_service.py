import smtplib
import traceback
from email.message import EmailMessage

from fastapi import HTTPException, status

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL

    async def send_email(self, to: str, subject: str, body: str):
        """Send a simple email using SMTP with enhanced error handling."""
        try:
            # Validate input
            if not self._is_valid_email(to):
                raise ValueError(f"Invalid email address: {to}")

            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to
            msg.set_content(body)

            # Explicitly start TLS encryption
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.ehlo()

            # Login with credentials
            server.login(self.smtp_username, self.smtp_password)

            # Send the email
            server.send_message(msg)
            server.quit()

            logger.info(f"Email sent to {to} successfully")

        except smtplib.SMTPAuthenticationError:
            logger.error(
                f"SMTP authentication failed for {to}. Check your credentials."
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid SMTP credentials",
            )
        except smtplib.SMTPServerDisconnected:
            logger.error(f"SMTP server disconnected for {to}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SMTP server connection lost",
            )
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error occurred: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email",
            )
        except Exception as e:
            logger.error(f"Unexpected error while sending email: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected error occurred while sending email",
            )

    async def send_registration_email(self, user_email: str, username: str):
        """Send a welcome email to a new user with enhanced error handling."""
        subject = "Welcome to HealthSync AI!"
        body = f"""
        Dear {username},

        Welcome to HealthSync AI! Thank you for joining our community.

        We're excited to have you on board. If you have any questions or need assistance,
        please don't hesitate to reach out to our support team.

        Best regards,
        The HealthSync AI Team
        """
        await self.send_email(user_email, subject, body)

    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        return "@" in email and email.endswith((".com", ".org", ".net", ".edu"))
