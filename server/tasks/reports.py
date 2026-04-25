from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from celery import shared_task
from flask import current_app

from mailer import send_email
from models import Appointment, Doctor


@shared_task(name="tasks.monthly_admin_report")
def monthly_admin_report() -> dict:
    tz = ZoneInfo(current_app.config.get("APP_TIMEZONE", "Asia/Kolkata"))
    now = datetime.now(tz)

    current_month_start = datetime(now.year, now.month, 1)
    if now.month == 1:
        month_start = datetime(now.year - 1, 12, 1)
        #month_start = current_month_start

    else:
        month_start = datetime(now.year, now.month - 1, 1)
        #month_start = current_month_start

    month_end = current_month_start
    #month_end = now

    doctors = Doctor.query.filter(Doctor.is_active.is_(True)).all()
    sent = 0

    for doctor in doctors:
        scheduled_appts = (
            Appointment.query.filter_by(doctor_id=doctor.id)
            .filter(Appointment.start_time >= month_start)
            .filter(Appointment.start_time < month_end)
            .all()
        )

        appts = (
            Appointment.query.filter_by(doctor_id=doctor.id)
            .filter(Appointment.status == "completed")
            .filter(Appointment.start_time >= month_start)
            .filter(Appointment.start_time < month_end)
            .order_by(Appointment.start_time.asc())
            .all()
        )

        cancelled_appts = (
            Appointment.query.filter_by(doctor_id=doctor.id)
            .filter(Appointment.status == "cancelled")
            .filter(Appointment.start_time >= month_start)
            .filter(Appointment.start_time < month_end)
            .all()
        )

        total_scheduled = len(scheduled_appts)
        total_completed = len(appts)
        total_cancelled = len(cancelled_appts)
        completion_rate = (total_completed / total_scheduled * 100) if total_scheduled else 0.0
        cancellation_rate = (total_cancelled / total_scheduled * 100) if total_scheduled else 0.0

        subject = f"HMS Monthly Activity Report: {month_start.strftime('%B %Y')}"
        rows = "".join(
            f"<tr><td>{a.start_time.strftime('%Y-%m-%d %H:%M')}</td>"
            f"<td>{a.patient.name if a.patient else ''}</td>"
            f"<td>{(a.diagnosis or '')}</td>"
            f"<td>{(a.prescription or '')}</td>"
            f"<td>{(a.medications_prescribed or '')}</td>"
            f"<td>{(a.tests_requested or '')}</td>"
            f"<td>{(a.follow_up_date.isoformat() if a.follow_up_date else '')}</td></tr>"
            for a in appts
        )
        body_html = (
            f"<h2>Monthly Activity Report</h2>"
            f"<p>Doctor: {doctor.name}</p>"
            f"<p>Month: {month_start.strftime('%B %Y')}</p>"
            "<h3>Monthly Summary</h3>"
            "<table border='1' cellpadding='6' cellspacing='0'>"
            "<thead><tr><th>Total Scheduled</th><th>Completed</th><th>Cancelled</th><th>Completion Rate</th><th>Cancellation Rate</th></tr></thead>"
            f"<tbody><tr><td>{total_scheduled}</td><td>{total_completed}</td><td>{total_cancelled}</td><td>{completion_rate:.2f}%</td><td>{cancellation_rate:.2f}%</td></tr></tbody></table>"
            f"<p>Completed appointments: {len(appts)}</p>"
            "<table border='1' cellpadding='6' cellspacing='0'>"
            "<thead><tr><th>Date/Time</th><th>Patient</th><th>Diagnosis</th><th>Prescription</th><th>Treatment</th><th>Tests</th><th>Follow-up</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>"
        )

        send_email(to=doctor.email, subject=subject, body_html=body_html, body_text=None)
        sent += 1

    return {"month": month_start.strftime("%Y-%m"), "doctors": len(doctors), "emails_sent": sent}
