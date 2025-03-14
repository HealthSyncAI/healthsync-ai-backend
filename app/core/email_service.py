import logging
import traceback

from fastapi import HTTPException, status
from mailjet_rest import Client

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.mailjet = Client(auth=(settings.MAILJET_API_KEY, settings.MAILJET_SECRET_KEY), version='v3.1')
        self.from_email = settings.MAILJET_FROM_EMAIL
        self.from_name = settings.MAILJET_FROM_NAME

    async def send_email(self, to: str, subject: str, body: str):
        """Send an email using Mailjet with enhanced error handling."""
        try:
            logger.info(f"Preparing to send email to: {to}")

            # Validate input
            if not self._is_valid_email(to):
                logger.error(f"Invalid email address: {to}")
                raise ValueError(f"Invalid email address: {to}")

            data = {
                'Messages': [
                    {
                        "From": {
                            "Email": self.from_email,
                            "Name": self.from_name
                        },
                        "To": [
                            {
                                "Email": to,
                                "Name": to
                            }
                        ],
                        "Subject": subject,
                        "TextPart": body,
                    }
                ]
            }

            logger.info(f"Mailjet data prepared for: {to}")
            logger.debug(f"Mailjet data: {data}")  # added log

            logger.info("Attempting to send email via Mailjet...")
            result = self.mailjet.send.create(data=data)
            logger.info(f"Mailjet result: {result.json()}")  # added log

            if result.status_code != 200:
                logger.error(f"Mailjet API error: {result.status_code}, {result.json()}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send email via Mailjet",
                )

            logger.info(f"Email sent to {to} successfully")

        except Exception as e:
            logger.error(f"Unexpected error while sending email: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected error occurred while sending email",
            )

    async def send_registration_email(self, user_email: str, username: str):
        """Send a welcome email to a new user using Mailjet."""
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