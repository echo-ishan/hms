from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

from celery import shared_task
from flask import current_app

from mailer import send_email
from models import Appointment


@shared_task(name="tasks.daily_appointment_reminders")
def daily_appointment_reminders() -> dict:
    tz = ZoneInfo(current_app.config.get("APP_TIMEZONE", "Asia/Kolkata"))
    target_date = datetime.now(tz).date()
    start = datetime.combine(target_date, time.min)
    end = datetime.combine(target_date, time.max)

    appointments = (
        Appointment.query.filter(Appointment.status == "booked")
        .filter(Appointment.start_time >= start)
        .filter(Appointment.start_time <= end)
        .all()
    )

    sent = 0
    for appt in appointments:
        if not appt.patient:
            continue
        subject = f"HMS Reminder: Appointment Today ({target_date.isoformat()})"
        body = (
            f"Hi {appt.patient.name},\n\n"
            f"You have a hospital visit scheduled for today ({target_date.isoformat()}).\n"
            f"Time: {appt.start_time.strftime('%H:%M')} - {appt.end_time.strftime('%H:%M')}\n"
            f"Doctor: {appt.doctor.name if appt.doctor else 'N/A'}\n\n"
            "Please visit the hospital at the scheduled time.\n"
        )
        send_email(to=appt.patient.email, subject=subject, body_text=body)
        sent += 1

    return {"target_date": target_date.isoformat(), "appointments": len(appointments), "emails_sent": sent}
