import datetime
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.email_service import EmailService
from app.db.database import get_db_session
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User

logger = logging.getLogger(__name__)


class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.email_service = EmailService()

    async def check_and_notify_appointments(self):
        """
        Checks for appointments scheduled for today and sends notifications
        to both patients and doctors.
        """
        logger.info("Running daily appointment notification check...")
        async for db in get_db_session():
            try:
                today_start = datetime.datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                today_end = datetime.datetime.now().replace(
                    hour=23, minute=59, second=59, microsecond=999
                )

                query = select(Appointment).where(
                    Appointment.start_time >= today_start,
                    Appointment.start_time <= today_end,
                    Appointment.status == AppointmentStatus.scheduled,
                )
                result = await db.execute(query)
                appointments = result.scalars().all()

                for appointment in appointments:
                    await self._notify_appointment(db, appointment)
                logger.info("Appointment notification check completed.")

            except Exception as e:
                logger.error(f"Error during appointment notification check: {e}")
                logger.exception(e)

    async def _notify_appointment(self, db: AsyncSession, appointment: Appointment):
        """
        Sends notification emails to both patient and doctor for a given appointment.
        """
        try:
            logger.info(f"Starting notification for appointment ID {appointment.id}")

            # Fetch patient and doctor details
            patient_query = select(User).where(User.id == appointment.patient_id)
            doctor_query = select(User).where(User.id == appointment.doctor_id)

            logger.info(f"Fetching patient with ID: {appointment.patient_id}")
            patient_result = await db.execute(patient_query)
            patient = patient_result.scalar_one_or_none()

            logger.info(f"Fetching doctor with ID: {appointment.doctor_id}")
            doctor_result = await db.execute(doctor_query)
            doctor = doctor_result.scalar_one_or_none()

            if not patient or not doctor:
                logger.warning(
                    f"Could not retrieve patient or doctor for appointment ID {appointment.id}"
                )
                return

            logger.info(
                f"Patient found: {patient.email if patient else 'None'}, Doctor found: {doctor.email if doctor else 'None'}"
            )

            # Construct email messages
            patient_subject = "Appointment Reminder"
            patient_body = f"""
            Dear {patient.first_name or patient.username},

            This is a reminder about your upcoming appointment with Dr. {doctor.first_name or doctor.username} today.

            Appointment Details:
            - Doctor: Dr. {doctor.first_name or doctor.username}
            - Time: {appointment.start_time.strftime("%Y-%m-%d %H:%M %Z")}
            - Telemedicine Link (if available): {appointment.telemedicine_url or 'N/A'}

            Please be ready for your appointment. If you need to reschedule or cancel, please do so as soon as possible.

            Best regards,
            HealthSync AI Team
            """

            doctor_subject = "Appointment Notification"
            doctor_body = f"""
            Dear Dr. {doctor.last_name or doctor.username},

            This is a notification for your appointment with patient {patient.first_name or patient.username} today.

            Appointment Details:
            - Patient: {patient.first_name or patient.username}
            - Time: {appointment.start_time.strftime("%Y-%m-%d %H:%M %Z")}
            - Telemedicine Link (if available): {appointment.telemedicine_url or 'N/A'}

            Please be prepared for your appointment.

            Best regards,
            HealthSync AI Team
            """

            # Send emails
            logger.info(f"Sending email to patient: {patient.email}")
            await self.email_service.send_email(
                patient.email, patient_subject, patient_body
            )
            logger.info(f"Sending email to doctor: {doctor.email}")
            await self.email_service.send_email(
                doctor.email, doctor_subject, doctor_body
            )

            logger.info(
                f"Notifications sent for appointment ID {appointment.id} (Patient: {patient.email}, Doctor: {doctor.email})"
            )

        except Exception as e:
            logger.error(f"Error notifying appointment {appointment.id}: {e}")
            logger.exception(e)

    def start_scheduler(self):
        """Starts the APScheduler."""
        self.scheduler.add_job(
            self.check_and_notify_appointments, "cron", hour=11, minute=35
        )  # Run at midnight
        self.scheduler.start()
        logger.info("Scheduler started...")

    def stop_scheduler(self):
        """Stops the APScheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped.")
        else:
            logger.info("Scheduler is not running.")


scheduler_service = SchedulerService()
