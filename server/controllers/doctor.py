from datetime import datetime, timedelta, timezone

from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required

from controllers import doctor_bp
from decorators import role_required
from extensions import cache, db
from http_utils import err, json_body, ok, parse_date, parse_datetime, parse_time, require_fields
from models import Appointment, Doctor, DoctorAvailability, Patient
from serializers import (
    appointment_doctor_view,
    appointment_patient_history_view,
    availability_slot,
    doctor_public,
)


def _current_doctor():
    doctor_id = get_jwt_identity()
    try:
        doctor_id_int = int(doctor_id)
    except (TypeError, ValueError):
        return None
    doctor = db.session.get(Doctor, doctor_id_int)
    return doctor


def _invalidate_doctor_cache():
    cache.clear()


@doctor_bp.get("/me")
@jwt_required()
@role_required("doctor")
def me():
    doctor = _current_doctor()
    if not doctor:
        return err("Doctor not found", status_code=404)
    return ok({"doctor": doctor_public(doctor)})


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------


@doctor_bp.get("/availability")
@jwt_required()
@role_required("doctor")
def list_availability():
    doctor = _current_doctor()
    if not doctor:
        return err("Doctor not found", status_code=404)

    date_str = request.args.get("date")
    query = DoctorAvailability.query.filter_by(doctor_id=doctor.id)
    if date_str:
        try:
            query = query.filter(DoctorAvailability.date == parse_date(date_str))
        except ValueError as exc:
            return err(str(exc), status_code=400)

    slots = query.order_by(DoctorAvailability.date.asc(), DoctorAvailability.start_time.asc()).all()
    return ok({"availability": [availability_slot(s) for s in slots]})


@doctor_bp.post("/availability")
@jwt_required()
@role_required("doctor")
def create_availability():
    doctor = _current_doctor()
    if not doctor:
        return err("Doctor not found", status_code=404)

    try:
        payload = json_body()
        require_fields(payload, ["date", "start_time", "end_time"])
        slot_date = parse_date(payload["date"])
        today = datetime.now(timezone.utc).date()
        max_allowed_date = today + timedelta(days=6)
        if slot_date < today:
            return err("Availability date cannot be in the past", status_code=400)
        if slot_date > max_allowed_date:
            return err("Availability can only be provided for the next 7 days", status_code=400)
        start = parse_time(payload["start_time"])
        end = parse_time(payload["end_time"])
        if start >= end:
            return err("start_time must be before end_time", status_code=400)

        overlap = (
            DoctorAvailability.query.filter_by(doctor_id=doctor.id, date=slot_date)
            .filter(DoctorAvailability.start_time < end)
            .filter(DoctorAvailability.end_time > start)
            .first()
        )
        if overlap:
            return err("Availability overlaps existing slot", status_code=409)

        slot = DoctorAvailability(doctor_id=doctor.id, date=slot_date, start_time=start, end_time=end)
        db.session.add(slot)
        db.session.commit()
        _invalidate_doctor_cache()
        return ok({"slot": availability_slot(slot)}, status_code=201)
    except ValueError as exc:
        return err(str(exc), status_code=400)


@doctor_bp.delete("/availability/<int:slot_id>")
@jwt_required()
@role_required("doctor")
def delete_availability(slot_id: int):
    doctor = _current_doctor()
    if not doctor:
        return err("Doctor not found", status_code=404)

    slot = DoctorAvailability.query.filter_by(id=slot_id, doctor_id=doctor.id).first()
    if not slot:
        return err("Slot not found", status_code=404)

    db.session.delete(slot)
    db.session.commit()
    _invalidate_doctor_cache()
    return ok({"msg": "Deleted"})


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------


@doctor_bp.get("/appointments")
@jwt_required()
@role_required("doctor")
def list_appointments():
    doctor = _current_doctor()
    if not doctor:
        return err("Doctor not found", status_code=404)

    status = request.args.get("status")
    from_dt = request.args.get("from")
    to_dt = request.args.get("to")

    query = Appointment.query.filter_by(doctor_id=doctor.id)
    if status:
        query = query.filter(Appointment.status == status)
    try:
        if from_dt:
            query = query.filter(Appointment.start_time >= parse_datetime(from_dt))
        if to_dt:
            query = query.filter(Appointment.start_time <= parse_datetime(to_dt))
    except ValueError as exc:
        return err(str(exc), status_code=400)

    appts = query.order_by(Appointment.start_time.desc()).all()
    return ok({"appointments": [appointment_doctor_view(a) for a in appts]})


@doctor_bp.patch("/appointments/<int:appointment_id>")
@jwt_required()
@role_required("doctor")
def update_appointment(appointment_id: int):
    doctor = _current_doctor()
    if not doctor:
        return err("Doctor not found", status_code=404)

    appt = Appointment.query.filter_by(id=appointment_id, doctor_id=doctor.id).first()
    if not appt:
        return err("Appointment not found", status_code=404)

    try:
        payload = json_body()
        if "status" in payload:
            new_status = payload["status"]
            if new_status not in Appointment.VALID_STATUSES:
                return err("Invalid status", status_code=400)
            if not appt.can_transition_to(new_status):
                return err("Invalid status transition", status_code=409)
            appt.status = new_status
            if new_status == "completed":
                appt.updated_at = datetime.now(timezone.utc)

        for field in ("diagnosis", "prescription", "tests_requested", "medications_prescribed", "notes", "visit_reason"):
            if field in payload:
                setattr(appt, field, payload[field])

        if "follow_up_date" in payload:
            appt.follow_up_date = parse_date(payload["follow_up_date"]) if payload["follow_up_date"] else None

        db.session.commit()
        _invalidate_doctor_cache()
        return ok({"appointment": appointment_doctor_view(appt)})
    except ValueError as exc:
        return err(str(exc), status_code=400)


@doctor_bp.get("/patient-history/<int:patient_id>")
@jwt_required()
@role_required("doctor")
def patient_history(patient_id: int):
    doctor = _current_doctor()
    if not doctor:
        return err("Doctor not found", status_code=404)

    patient = db.session.get(Patient, patient_id)
    if not patient:
        return err("Patient not found", status_code=404)

    has_assignment = Appointment.query.filter_by(doctor_id=doctor.id, patient_id=patient_id).first()
    if not has_assignment:
        return err("You are not assigned to this patient", status_code=403)

    appts = (
        Appointment.query.filter_by(patient_id=patient_id, doctor_id=doctor.id, status="completed")
        .order_by(Appointment.start_time.asc())
        .all()
    )

    return ok(
        {
            "patient": patient.to_dict(),
            "appointments": [appointment_patient_history_view(a) for a in appts],
        }
    )
