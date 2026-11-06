"""SMTP delivery for approved LEADFLOW AI follow-up messages."""

import os

from dotenv import load_dotenv
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from pydantic import EmailStr

load_dotenv()


def _mail_config():
    required = ("MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_FROM")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError(
            "Email is not configured. Add " + ", ".join(missing) + " to backend/.env."
        )

    return ConnectionConfig(
        MAIL_USERNAME=os.environ["MAIL_USERNAME"],
        MAIL_PASSWORD=os.environ["MAIL_PASSWORD"],
        MAIL_FROM=os.environ["MAIL_FROM"],
        MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
        MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "true").lower() == "true",
        MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "false").lower() == "true",
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )


async def send_lead_email(customer_email: str, customer_name: str, message: str):
    """Send a plain-text follow-up email using configured SMTP credentials."""
    email_message = MessageSchema(
        subject="Follow-up regarding your enquiry",
        recipients=[EmailStr(customer_email)],
        body=(
            f"Hi {customer_name},\n\n{message}\n\n"
            "Best regards,\nLEADFLOW AI Team"
        ),
        subtype="plain",
    )

    mailer = FastMail(_mail_config())
    await mailer.send_message(email_message)
    return True
