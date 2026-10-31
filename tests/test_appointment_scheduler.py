from datetime import datetime

from main import build_email_message, is_due_now


def test_build_email_message_contains_client_name_and_reminder_text():
    body = build_email_message("Alice Johnson", "alice@example.com", "2026-10-03 10:00:00")

    assert "Alice Johnson" in body
    assert "appointment" in body.lower()
    assert "alice@example.com" in body


def test_is_due_now_handles_match_at_exact_time():
    scheduled_time = datetime(2026, 10, 3, 10, 0, 0)
    now = datetime(2026, 10, 3, 10, 0, 0)

    assert is_due_now(scheduled_time, now) is True
