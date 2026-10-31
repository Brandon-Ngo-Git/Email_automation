# Automated Client Appointment Reminder System

This project watches a MySQL database for appointment rows and emails each client at the scheduled time as a reminder.

## Database schema

```sql
CREATE DATABASE IF NOT EXISTS client_reminders;
USE client_reminders;

CREATE TABLE IF NOT EXISTS appointments (
  id INT AUTO_INCREMENT PRIMARY KEY,
  client_name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  scheduled_at DATETIME NOT NULL,
  status ENUM('pending', 'sent', 'failed') NOT NULL DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Add clients like this:

```sql
INSERT INTO appointments (client_name, email, scheduled_at)
VALUES ('Alice Johnson', 'alice@example.com', '2026-10-03 10:00:00');
```

## Setup

1. Copy `.env.example` to `.env`.
2. Fill in your MySQL connection details and SMTP credentials.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the service:

```bash
python main.py
```

The application checks the database every 60 seconds and sends reminders for any appointment whose `scheduled_at` time has arrived.

## Notes

- Gmail requires an app password instead of a normal account password for SMTP.
- The service marks each reminder as `sent` after successfully delivering the email to avoid duplicate sends.
