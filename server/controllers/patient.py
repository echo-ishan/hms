from flask import current_app
from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required

from controllers import patient_bp
from decorators import role_required
from extensions import cache, db
from http_utils import err, json_body, normalize_gender, ok, parse_date, parse_datetime, require_fields
from models import Appointment, Department, Doctor, DoctorAvailability, Patient
from serializers import (
    appointment_patient_view,
    department_public,
    doctor_public,
    availability_slot,
    patient_public,
)
from tasks.exports import export_completed_treatments_csv


EXPORT_TASK_OWNER_TTL_SECONDS = 24 * 60 * 60


def _export_task_owner_cache_key(task_id: str) -> str:
    return f"export-task-owner:{task_id}"


def _current_patient():
    patient_id = get_jwt_identity()
    try:
        patient_id_int = int(patient_id)
    except (TypeError, ValueError):
        return None
    patient = db.session.get(Patient, patient_id_int)
    return patient


def _invalidate_patient_cache():
    cache.clear()


@patient_bp.get("/me")
@jwt_required()
@role_required("patient")
def me():
    patient = _current_patient()
    if not patient:
        return err("Patient not found", status_code=404)
    return ok({"patient": patient_public(patient)})


@patient_bp.patch("/me")
@jwt_required()
@role_required("patient")
def update_me():
    patient = _current_patient()
    if not patient:
        return err("Patient not found", status_code=404)

    try:
        payload = json_body()

        if "name" in payload:
            patient.name = payload["name"].strip()
        if "dob" in payload:
            patient.dob = parse_date(payload["dob"])
        if "contact_number" in payload:
            patient.contact_number = payload["contact_number"].strip()
        if "gender" in payload:
            patient.gender = normalize_gender(payload["gender"])
        if "blood_group" in payload:
            patient.blood_group = payload["blood_group"] or None
        if "past_medical_history" in payload:
            patient.past_medical_history = payload["past_medical_history"] or None
        if "emergency_contact" in payload:
            patient.emergency_contact = payload["emergency_contact"] or None
        if "address" in payload:
            patient.address = payload["address"] or None
        if "password" in payload and payload["password"]:
            patient.set_password(payload["password"])

        db.session.commit()
        return ok({"patient": patient_public(patient)})
    except ValueError as exc:
        return err(str(exc), status_code=400)


@patient_bp.get("/departments")
@cache.cached(timeout=600)
def list_departments():
    departments = Department.query.order_by(Department.name.asc()).all()
    return ok({"departments": [department_public(d) for d in departments]})


@patient_bp.get("/doctors")
@cache.cached(timeout=180, query_string=True)
def list_doctors():
    q = request.args.get("q", "").strip()
    dept_id = request.args.get("department_id")

    query = Doctor.query.filter(Doctor.is_active.is_(True))
    if dept_id:
        query = query.filter(Doctor.department_id == int(dept_id))
    if q:
        like = f"%{q}%"
        query = query.filter((Doctor.name.ilike(like)) | (Doctor.email.ilike(like)))

    doctors = query.order_by(Doctor.name.asc()).all()
    return ok({"doctors": [doctor_public(d) for d in doctors]})


@patient_bp.get("/doctors/<int:doctor_id>")
@cache.cached(timeout=300)
def get_doctor(doctor_id: int):
    doctor = db.session.get(Doctor, doctor_id)
    if not doctor or not doctor.is_active:
        return err("Doctor not found", status_code=404)
    return ok({"doctor": doctor_public(doctor)})


@patient_bp.get("/doctors/<int:doctor_id>/availability")
@cache.cached(timeout=30, query_string=True)
def doctor_availability(doctor_id: int):
    doctor = db.session.get(Doctor, doctor_id)
    if not doctor or not doctor.is_active:
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


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------


@patient_bp.get("/appointments")
@jwt_required()
@role_required("patient")
def list_appointments():
    patient = _current_patient()
    if not patient:
        return err("Patient not found", status_code=404)

    status = request.args.get("status")
    query = Appointment.query.filter_by(patient_id=patient.id)
    if status:
        query = query.filter(Appointment.status == status)

    appts = query.order_by(Appointment.start_time.desc()).all()
    return ok({"appointments": [appointment_patient_view(a) for a in appts]})


@patient_bp.post("/appointments")
@jwt_required()
@role_required("patient")
def book_appointment():
    patient = _current_patient()
    if not patient:
        return err("Patient not found", status_code=404)

    try:
        payload = json_body()
        require_fields(payload, ["doctor_id", "start_time", "end_time"])
        doctor = db.session.get(Doctor, int(payload["doctor_id"]))
        if not doctor or not doctor.is_active:
            return err("Doctor not found", status_code=404)

        start_dt = parse_datetime(payload["start_time"])
        end_dt = parse_datetime(payload["end_time"])
        if start_dt >= end_dt:
            return err("start_time must be before end_time", status_code=400)

        day = start_dt.date()
        within_slot = (
            DoctorAvailability.query.filter_by(doctor_id=doctor.id, date=day)
            .filter(DoctorAvailability.start_time <= start_dt.time())
            .filter(DoctorAvailability.end_time >= end_dt.time())
            .first()
        )
        if not within_slot:
            return err("Requested time is outside doctor's availability", status_code=409)

        overlap = (
            Appointment.query.filter_by(doctor_id=doctor.id)
            .filter(Appointment.status == "booked")
            .filter(Appointment.start_time < end_dt)
            .filter(Appointment.end_time > start_dt)
            .first()
        )
        if overlap:
            return err("Doctor already has an appointment in this time", status_code=409)

        appt = Appointment(
            doctor_id=doctor.id,
            patient_id=patient.id,
            start_time=start_dt,
            end_time=end_dt,
            status="booked",
            visit_reason=payload.get("visit_reason"),
        )
        db.session.add(appt)
        db.session.commit()
        _invalidate_patient_cache()
        return ok({"appointment": appointment_patient_view(appt)}, status_code=201)
    except ValueError as exc:
        return err(str(exc), status_code=400)


@patient_bp.patch("/appointments/<int:appointment_id>")
@jwt_required()
@role_required("patient")
def update_appointment(appointment_id: int):
    patient = _current_patient()
    if not patient:
        return err("Patient not found", status_code=404)

    appt = Appointment.query.filter_by(id=appointment_id, patient_id=patient.id).first()
    if not appt:
        return err("Appointment not found", status_code=404)

    try:
        payload = json_body()
        if payload.get("status") == "cancelled":
            if not appt.can_transition_to("cancelled"):
                return err("Cannot cancel this appointment", status_code=409)
            appt.status = "cancelled"
        elif "status" in payload:
            return err("Only cancellation is allowed", status_code=400)

        if "visit_reason" in payload:
            appt.visit_reason = payload["visit_reason"]

        db.session.commit()
        _invalidate_patient_cache()
        return ok({"appointment": appointment_patient_view(appt)})
    except ValueError as exc:
        return err(str(exc), status_code=400)


# ---------------------------------------------------------------------------
# Async exports (Celery)
# ---------------------------------------------------------------------------


@patient_bp.post("/exports/treatments")
@jwt_required()
@role_required("patient")
def export_treatments_csv():
    patient = _current_patient()
    if not patient:
        return err("Patient not found", status_code=404)

    celery = current_app.extensions.get("celery")
    if not celery:
        return err("Celery not configured", status_code=500)

    async_result = celery.send_task("tasks.export_completed_treatments_csv", args=[patient.id])
    cache.set(_export_task_owner_cache_key(async_result.id), patient.id, timeout=EXPORT_TASK_OWNER_TTL_SECONDS)
    return ok({"task_id": async_result.id}, status_code=202)


@patient_bp.get("/exports/<string:task_id>")
@jwt_required()
@role_required("patient")
def export_status(task_id: str):
    patient = _current_patient()
    if not patient:
        return err("Patient not found", status_code=404)

    celery = current_app.extensions.get("celery")
    if not celery:
        return err("Celery not configured", status_code=500)

    owner_id = cache.get(_export_task_owner_cache_key(task_id))
    if owner_id is None:
        return err("Task not found", status_code=404)
    if str(owner_id) != str(patient.id):
        return err("Forbidden", status_code=403)

    result = celery.AsyncResult(task_id)
    payload = {"task_id": task_id, "state": result.state}
    if result.successful():
        payload["result"] = result.result
    elif result.failed():
        payload["error"] = str(result.result)
    return ok(payload)
