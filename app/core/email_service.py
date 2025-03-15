import logging
import traceback
import smtplib
from email.mime.text import MIMEText

from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME

    async def send_email(self, to: str, subject: str, body: str):
        """Send an email using SMTP with enhanced error handling."""
        try:
            logger.info(f"Preparing to send email to: {to}")
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to

            logger.info(f"SMTP data prepared for: {to}")
            logger.debug(f"SMTP message: {msg}")

            logger.info("Attempting to send email via SMTP...")

            try:
                with smtplib.SMTP(
                    self.smtp_server, self.smtp_port, timeout=10
                ) as server:  # added timeout
                    logger.info("SMTP connection established")
                    server.starttls()
                    logger.info("TLS started")
                    server.login(self.smtp_username, self.smtp_password)
                    logger.info("SMTP login successful")
                    server.sendmail(self.from_email, to, msg.as_string())
                    logger.info("Email sent successfully")

            except smtplib.SMTPAuthenticationError:
                logger.error("SMTP Authentication failed. Check your credentials.")
            except smtplib.SMTPException as e:
                logger.error(f"SMTP error: {str(e)}")
            except TimeoutError:
                logger.error("SMTP connection timed out.")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")

            logger.info(f"Email sent to {to} successfully")

        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP Authentication failed. Check your credentials.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SMTP Authentication failed.",
            )
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email via SMTP",
            )
        except Exception as e:
            logger.error(f"Unexpected error while sending email: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unexpected error occurred while sending email",
            )

    async def send_registration_email(self, user_email: str, username: str):
        """Send a welcome email to a new user using SMTP."""
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
