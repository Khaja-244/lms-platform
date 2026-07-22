import logging
import os
import smtplib
from email.message import EmailMessage
from typing import Iterable

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def email_is_configured() -> bool:
    return all(
        [
            os.getenv("SMTP_HOST"),
            os.getenv("SMTP_USERNAME"),
            os.getenv("SMTP_PASSWORD"),
            os.getenv("DEFAULT_FROM_EMAIL"),
        ]
    )


def send_email(
    to_email: str,
    subject: str,
    body: str,
    attachments: Iterable[tuple[str, bytes, str]] | None = None,
) -> bool:
    if not email_is_configured():
        logger.info("Email skipped because SMTP settings are not configured.")
        return False

    message = EmailMessage()
    message["From"] = os.getenv("DEFAULT_FROM_EMAIL")
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    for filename, content, mime_type in attachments or []:
        maintype, subtype = mime_type.split("/", 1)
        message.add_attachment(content, maintype=maintype, subtype=subtype, filename=filename)

    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    use_tls = os.getenv("SMTP_USE_TLS", "True").lower() == "true"

    try:
        with smtplib.SMTP(host, port, timeout=20) as server:
            if use_tls:
                server.starttls()
            server.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD"))
            server.send_message(message)
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        return False


def notification_subject(notification_type: str) -> str:
    subjects = {
        "plan_expiry": "Subscription update",
        "course_update": "Course update",
        "instructor_message": "Instructor message",
        "system": "Platform notification",
    }
    return subjects.get(notification_type, "Platform notification")
