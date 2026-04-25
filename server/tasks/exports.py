from __future__ import annotations

import csv
import os
from datetime import datetime

from celery import shared_task
from flask import current_app

from mailer import send_email
from extensions import db
from models import Appointment, Patient


@shared_task(name="tasks.export_completed_treatments_csv")
def export_completed_treatments_csv(patient_id: int) -> dict:
    patient = db.session.get(Patient, patient_id)
    if not patient:
        return {"ok": False, "msg": "Patient not found"}

    appts = (
        Appointment.query.filter_by(patient_id=patient.id)
        .filter(Appointment.status == "completed")
        .order_by(Appointment.start_time.asc())
        .all()
    )

    export_dir = os.path.join(current_app.instance_path, "exports")
    os.makedirs(export_dir, exist_ok=True)
    filename = f"treatments_patient_{patient.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    path = os.path.join(export_dir, filename)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "user_id",
                "username",
                "appointment_id",
                "appointment_date",
                "consulting_doctor",
                "visit_reason",
                "diagnosis",
                "treatment",
                "tests_requested",
                "next_visit_date",
                "notes",
            ]
        )
        for a in appts:
            writer.writerow(
                [
                    patient.id,
                    patient.name,
                    a.id,
                    a.start_time.isoformat() if a.start_time else "",
                    a.doctor.name if a.doctor else "",
                    a.visit_reason or "",
                    a.diagnosis or "",
                    a.prescription or "",
                    a.tests_requested or "",
                    a.follow_up_date.isoformat() if a.follow_up_date else "",
                    a.notes or "",
                ]
            )

    send_email(
        to=patient.email,
        subject="HMS Export: Completed Treatment History (CSV)",
        body_text=(
            f"Hi {patient.name},\n\n"
            "Your CSV export is ready.\n"
            f"File: {filename}\n\n"
            "If you are running locally, you can find it under the server instance folder.\n"
        ),
    )

    return {"ok": True, "patient_id": patient.id, "appointments": len(appts), "file": filename}

