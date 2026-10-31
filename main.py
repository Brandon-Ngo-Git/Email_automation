import os
import smtplib
import time
from datetime import datetime
from email.message import EmailMessage

import mysql.connector
from dotenv import load_dotenv


load_dotenv()


def build_email_message(client_name: str, client_email: str, scheduled_time: str) -> str:
    """Return the appointment reminder content for the email body."""
    formatted_time = datetime.fromisoformat(scheduled_time).strftime("%Y-%m-%d at %H:%M")
    return (
        f"Hello {client_name},\n\n"
        f"This is a reminder that your appointment is scheduled for {formatted_time}.\n"
        f"Please make sure you are ready for your appointment at that time.\n\n"
        f"Thank you,\n"
        f"Your clinic team\n\n"
        f"Client email: {client_email}"
    )


def is_due_now(scheduled_time: datetime, now: datetime | None = None) -> bool:
    """Return True if a reminder should be sent at the current time."""
    if now is None:
        now = datetime.now()
    return scheduled_time <= now


def get_db_connection():
    """Create a MySQL connection using environment-based configuration."""
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "client_reminders"),
        autocommit=True,
        charset="utf8mb4",
    )


def ensure_database_schema(connection):
    """Create the appointments table if it does not already exist."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS appointments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                client_name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                scheduled_at DATETIME NOT NULL,
                status ENUM('pending', 'sent', 'failed') NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def fetch_due_appointments(connection, now: datetime | None = None):
    """Return rows that should be emailed now."""
    if now is None:
        now = datetime.now()

    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    with connection.cursor(dictionary=True) as cursor:
        cursor.execute(
            """
            SELECT id, client_name, email, scheduled_at
            FROM appointments
            WHERE status = 'pending' AND scheduled_at <= %s
            ORDER BY scheduled_at ASC
            """,
            (current_time,),
        )
        return cursor.fetchall()


def send_appointment_email(client_name: str, client_email: str, scheduled_at: datetime):
    """Send an appointment reminder email using SMTP."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        raise ValueError("SMTP_USER and SMTP_PASSWORD must be configured in the environment.")

    message = EmailMessage()
    message["Subject"] = f"Appointment Reminder for {client_name}"
    message["From"] = smtp_user
    message["To"] = client_email
    message.set_content(
        f"Hello {client_name},\n\n"
        f"This is a reminder that your appointment is scheduled for {scheduled_at.strftime('%Y-%m-%d at %H:%M')}.\n"
        "Please make sure you are ready at that time.\n\n"
        "Thank you,\n"
        "Your clinic team"
    )

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(message)

    return True


def mark_appointment_as_sent(connection, appointment_id: int):
    """Update the appointment so it is not sent again."""
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE appointments SET status = 'sent' WHERE id = %s",
            (appointment_id,),
        )


def poll_for_due_appointments(interval_seconds: int = 60):
    """Continuously watch the database and send reminders for appointments that are due."""
    connection = get_db_connection()
    ensure_database_schema(connection)

    while True:
        try:
            due_appointments = fetch_due_appointments(connection)
            for appointment in due_appointments:
                scheduled_at = datetime.strptime(appointment["scheduled_at"], "%Y-%m-%d %H:%M:%S")
                try:
                    send_appointment_email(
                        appointment["client_name"],
                        appointment["email"],
                        scheduled_at,
                    )
                    mark_appointment_as_sent(connection, appointment["id"])
                    print(f"Sent reminder to {appointment['email']} for {appointment['client_name']}")
                except Exception as exc:  # pragma: no cover - runtime email failure
                    print(f"Could not send reminder to {appointment['email']}: {exc}")
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "UPDATE appointments SET status = 'failed' WHERE id = %s",
                            (appointment["id"],),
                        )
        except Exception as exc:  # pragma: no cover - connection failure handling
            print(f"Database polling error: {exc}")

        time.sleep(interval_seconds)


def main():
    """Start the database polling loop."""
    print("Appointment reminder service started. Watching for due appointments...")
    poll_for_due_appointments(interval_seconds=60)


if __name__ == "__main__":
    main()
