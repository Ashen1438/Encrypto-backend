import mimetypes
import os
import smtplib

from datetime import datetime
from email.message import EmailMessage


def send_security_alert_email(
    *,
    incident_id: int,
    incident_type: str,
    reason: str,
    device_info: str | None,
    ip_address: str | None,
    created_at: datetime,
    recipient_email: str | None = None,
    image_path: str | None = None,
) -> bool:
    try:
        smtp_host = os.getenv(
            "SMTP_HOST",
            "smtp.gmail.com",
        )

        smtp_port = int(
            os.getenv("SMTP_PORT", "587")
        )

        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv(
            "SMTP_APP_PASSWORD"
        )

        alert_email = (
            recipient_email
            or os.getenv("ALERT_EMAIL")
        )

        if not smtp_user:
            print(
                "Email alert skipped: "
                "SMTP_USER is missing"
            )
            return False

        if not smtp_password:
            print(
                "Email alert skipped: "
                "SMTP_APP_PASSWORD is missing"
            )
            return False

        if not alert_email:
            print(
                "Email alert skipped: "
                "recipient email is missing"
            )
            return False

        message = EmailMessage()

        message["Subject"] = (
            "Encrypto Security Alert: "
            "Unauthorized Access Attempt"
        )

        message["From"] = smtp_user
        message["To"] = alert_email

        formatted_time = created_at.strftime(
            "%d/%m/%Y %I:%M:%S %p"
        )

        message.set_content(
            f"""
Encrypto detected an unauthorized access attempt.

Incident ID: {incident_id}
Incident type: {incident_type}
Reason: {reason}
Device: {device_info or "Unknown device"}
IP address: {ip_address or "Unknown"}
Date and time: {formatted_time}

Please open the Encrypto Security page for more details.

This is an automated security alert from Encrypto.
""".strip()
        )

        if image_path and os.path.exists(image_path):
            mime_type, _ = mimetypes.guess_type(
                image_path
            )

            if mime_type:
                main_type, sub_type = (
                    mime_type.split("/", 1)
                )
            else:
                main_type = "application"
                sub_type = "octet-stream"

            with open(image_path, "rb") as image_file:
                message.add_attachment(
                    image_file.read(),
                    maintype=main_type,
                    subtype=sub_type,
                    filename=os.path.basename(
                        image_path
                    ),
                )

        with smtplib.SMTP(
            smtp_host,
            smtp_port,
            timeout=10,
        ) as smtp_server:
            smtp_server.ehlo()
            smtp_server.starttls()
            smtp_server.ehlo()

            smtp_server.login(
                smtp_user,
                smtp_password,
            )

            smtp_server.send_message(message)

        print(
            "Security alert email sent to "
            f"{alert_email}"
        )

        return True

    except Exception as error:
        print(
            "Security alert email failed: "
            f"{error}"
        )

        return False