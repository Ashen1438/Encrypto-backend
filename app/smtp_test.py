import os
import smtplib
import ssl

from email.message import EmailMessage


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

alert_email = os.getenv("ALERT_EMAIL")


if not smtp_user:
    raise ValueError("SMTP_USER is missing")

if not smtp_password:
    raise ValueError(
        "SMTP_APP_PASSWORD is missing"
    )

if not alert_email:
    raise ValueError("ALERT_EMAIL is missing")


message = EmailMessage()

message["Subject"] = (
    "Encrypto Local SMTP Test"
)

message["From"] = smtp_user
message["To"] = alert_email

message.set_content(
    """
This is a local SMTP test from Encrypto.

If you received this message, Gmail SMTP and the
App Password are working correctly.
""".strip()
)


try:
    print(
        f"Connecting to {smtp_host}:{smtp_port}..."
    )

    ssl_context = ssl.create_default_context()

    with smtplib.SMTP(
        smtp_host,
        smtp_port,
        timeout=20,
    ) as smtp_server:
        smtp_server.ehlo()

        print("Starting TLS...")

        smtp_server.starttls(
            context=ssl_context
        )

        smtp_server.ehlo()

        print("Logging in...")

        smtp_server.login(
            smtp_user,
            smtp_password,
        )

        print("Sending test email...")

        smtp_server.send_message(message)

    print(
        f"SUCCESS: Email sent to {alert_email}"
    )

except Exception as error:
    print(
        f"FAILED: {type(error).__name__}: "
        f"{error}"
    )