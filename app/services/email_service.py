import base64
import os

from datetime import datetime

import requests


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
        api_key = os.getenv("BREVO_API_KEY")

        sender_email = os.getenv(
            "ALERT_FROM_EMAIL"
        )

        fallback_email = os.getenv(
            "ALERT_EMAIL"
        )

        alert_email = (
            recipient_email
            or fallback_email
        )

        if not api_key:
            print(
                "Email alert skipped: "
                "BREVO_API_KEY is missing"
            )
            return False

        if not sender_email:
            print(
                "Email alert skipped: "
                "ALERT_FROM_EMAIL is missing"
            )
            return False

        if not alert_email:
            print(
                "Email alert skipped: "
                "recipient email is missing"
            )
            return False

        formatted_time = created_at.strftime(
            "%d/%m/%Y %I:%M:%S %p"
        )

        email_body = f"""
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

        payload = {
            "sender": {
                "name": "Encrypto Security",
                "email": sender_email,
            },
            "to": [
                {
                    "email": alert_email,
                }
            ],
            "subject": (
                "Encrypto Security Alert: "
                "Unauthorized Access Attempt"
            ),
            "textContent": email_body,
        }

        if (
            image_path
            and os.path.exists(image_path)
        ):
            with open(
                image_path,
                "rb",
            ) as image_file:
                encoded_image = base64.b64encode(
                    image_file.read()
                ).decode("utf-8")

            payload["attachment"] = [
                {
                    "name": os.path.basename(
                        image_path
                    ),
                    "content": encoded_image,
                }
            ]

        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "content-type": "application/json",
                "api-key": api_key,
            },
            json=payload,
            timeout=20,
        )

        if response.status_code in {
            200,
            201,
            202,
        }:
            print(
                "Security alert email sent to "
                f"{alert_email}"
            )
            return True

        print(
            "Security alert email failed: "
            f"{response.status_code} "
            f"{response.text}"
        )

        return False

    except Exception as error:
        print(
            "Security alert email failed: "
            f"{type(error).__name__}: "
            f"{error}"
        )
        return False