import os

from dotenv import load_dotenv
from fastapi_mail import (
    FastMail,
    MessageSchema,
    ConnectionConfig,
)
from pydantic import EmailStr

load_dotenv()


conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "True").lower() == "true",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "False").lower() == "true",
    USE_CREDENTIALS=True,
)


async def send_lead_email(
    customer_email: str,
    customer_name: str,
    message: str,
):
    email = MessageSchema(
        subject="Follow-up regarding your enquiry",
        recipients=[EmailStr(customer_email)],
        body=f"""
Hi {customer_name},

{message}

Best regards,
LEADFLOW AI Team
""",
        subtype="plain",
    )

    fm = FastMail(conf)

    await fm.send_message(email)

    return True