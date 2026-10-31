# Automated Client Appointment Reminder System

This project uses n8n to collect Google Forms responses into MySQL and a Python service to email appointment reminders when they are due. Docker Compose can run n8n, MySQL, and the reminder service together.

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

## Run with Docker Compose

From the project directory, copy `.env.example` to `.env` and replace the placeholder passwords and SMTP values. Set `TZ` to the timezone used for appointment times (the default is `UTC`). Then start all three services:

```bash
docker compose up -d --build
```

Open n8n at <http://localhost:5678> and complete its initial setup. MySQL and n8n data are stored in persistent Docker volumes.

### Connect Google Forms to MySQL

1. In Google Forms, link responses to a Google Sheet.
2. In n8n, create a workflow with a **Google Sheets Trigger** for new response rows.
3. Add a **MySQL** node configured with host `mysql`, port `3306`, database `client_reminders` (or the value of `MYSQL_DATABASE`), and the `MYSQL_USER` / `MYSQL_PASSWORD` values from `.env`.
4. Insert each response into the `appointments` table. Map the form fields to `client_name`, `email`, and `scheduled_at`. Leave `id`, `status`, and `created_at` to their database defaults so new appointments are pending.
5. Activate the workflow and submit a test response. Verify it appears in MySQL with `status = 'pending'`.

The Python reminder service connects to this same database and checks for due pending appointments every 60 seconds. Avoid running another reminder sender against the same records, as that can send duplicates. Ensure form dates, MySQL, and the `TZ` setting use a consistent timezone.

View logs or stop the services with:

```bash
docker compose logs -f reminder
docker compose logs -f n8n
docker compose down
```

`docker compose down` stops and removes the containers but preserves the named MySQL and n8n data volumes. Do not remove those volumes unless you intend to delete the stored data. The `.env` file is excluded from the Docker build context and Git; do not commit it.

## Run the Python service without Docker

For a local Python run, install the packages and configure the MySQL and SMTP environment variables described in `.env.example`:

```bash
pip install -r requirements.txt
python main.py
```

In this setup, configure `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DATABASE` for your existing MySQL server. The Compose-specific `MYSQL_ROOT_PASSWORD` is only used to initialize its MySQL container.

## Notes

- Gmail requires an app password instead of a normal account password for SMTP.
- The service marks each reminder as `sent` after successfully delivering the email to avoid duplicate sends.
