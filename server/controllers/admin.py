from flask import request
from flask_jwt_extended import jwt_required

from controllers import admin_bp
from decorators import role_required
from extensions import cache, db
from http_utils import err, json_body, normalize_gender, ok, parse_date, parse_years_experience, require_fields
from models import Appointment, Department, Doctor, Patient, User
from serializers import (
    appointment_admin_view,
    department_admin,
    doctor_admin,
    patient_admin,
)


def _invalidate_admin_cache():
    cache.clear()


@admin_bp.get("/stats")
@jwt_required()
@role_required("admin")
@cache.cached(timeout=120)
def stats():
    return ok(
        {
            "counts": {
                "users": User.query.count(),
                "doctors": Doctor.query.count(),
                "patients": Patient.query.count(),
                "departments": Department.query.count(),
            }
        }
    )


@admin_bp.get("/appointments")
@jwt_required()
@role_required("admin")
@cache.cached(timeout=60, query_string=True)
def list_appointments():
    status = request.args.get("status", "").strip().lower()
    q = request.args.get("q", "").strip()
    limit_arg = request.args.get("limit", "").strip()

    limit = None
    if limit_arg:
        try:
            limit = max(1, min(int(limit_arg), 100))
        except ValueError:
            return err("Invalid limit", status_code=400)

    query = Appointment.query
    if status:
        query = query.filter(Appointment.status == status)
    if q:
        like = f"%{q}%"
        query = query.filter(
            Appointment.patient.has((Patient.name.ilike(like)) | (Patient.email.ilike(like)))
            | Appointment.doctor.has((Doctor.name.ilike(like)) | (Doctor.email.ilike(like)))
        )

    query = query.order_by(Appointment.start_time.desc())
    if limit:
        query = query.limit(limit)
    appointments = query.all()
    return ok({"appointments": [appointment_admin_view(a) for a in appointments]})


@admin_bp.patch("/appointments/<int:appointment_id>")
@jwt_required()
@role_required("admin")
def update_appointment(appointment_id: int):
    appt = db.session.get(Appointment, appointment_id)
    if not appt:
        return err("Appointment not found", status_code=404)

    try:
        payload = json_body()
        if payload.get("status") != "cancelled":
            return err("Only cancellation is allowed", status_code=400)
        if appt.status != "booked":
            return err("Only booked appointments can be cancelled", status_code=409)

        appt.status = "cancelled"
        db.session.commit()
        _invalidate_admin_cache()
        return ok({"appointment": appointment_admin_view(appt)})
    except ValueError as exc:
        return err(str(exc), status_code=400)


# ---------------------------------------------------------------------------
# Departments
# ---------------------------------------------------------------------------


@admin_bp.get("/departments")
@jwt_required()
@role_required("admin")
@cache.cached(timeout=300)
def list_departments():
    departments = Department.query.order_by(Department.name.asc()).all()
    return ok({"departments": [department_admin(d) for d in departments]})


@admin_bp.post("/departments")
@jwt_required()
@role_required("admin")
def create_department():
    try:
        payload = json_body()
        require_fields(payload, ["name"])
        name = payload["name"].strip()

        if Department.query.filter_by(name=name).first():
            return err("Department already exists", status_code=409)

        dept = Department(name=name, description=payload.get("description"))
        db.session.add(dept)
        db.session.commit()
        _invalidate_admin_cache()
        return ok({"department": department_admin(dept)}, status_code=201)
    except ValueError as exc:
        return err(str(exc), status_code=400)


# ---------------------------------------------------------------------------
# Doctors
# ---------------------------------------------------------------------------


@admin_bp.get("/doctors")
@jwt_required()
@role_required("admin")
@cache.cached(timeout=60, query_string=True)
def list_doctors():
    q = request.args.get("q", "").strip()
    dept_id = request.args.get("department_id")

    query = Doctor.query
    if dept_id:
        query = query.filter(Doctor.department_id == int(dept_id))
    if q:
        like = f"%{q}%"
        query = query.filter((Doctor.name.ilike(like)) | (Doctor.email.ilike(like)))

    doctors = query.order_by(Doctor.created_at.desc()).all()
    return ok({"doctors": [doctor_admin(d) for d in doctors]})


@admin_bp.post("/doctors")
@jwt_required()
@role_required("admin")
def create_doctor():
    try:
        payload = json_body()
        require_fields(payload, ["email", "password", "name"])
        email = payload["email"].strip().lower()

        if User.query.filter_by(email=email).first():
            return err("Email already registered", status_code=409)

        doctor = Doctor(
            email=email,
            name=payload["name"].strip(),
            department_id=payload.get("department_id"),
            license_number=payload.get("license_number"),
            contact_number=payload.get("contact_number"),
            years_experience=parse_years_experience(payload.get("years_experience")),
            bio=payload.get("bio"),
            is_active=bool(payload.get("is_active", True)),
        )
        doctor.set_password(payload["password"])
        db.session.add(doctor)
        db.session.commit()
        _invalidate_admin_cache()
        return ok({"doctor": doctor_admin(doctor)}, status_code=201)
    except ValueError as exc:
        return err(str(exc), status_code=400)


@admin_bp.get("/doctors/<int:doctor_id>")
@jwt_required()
@role_required("admin")
def get_doctor(doctor_id: int):
    doctor = db.session.get(Doctor, doctor_id)
    if not doctor:
        return err("Doctor not found", status_code=404)
    return ok({"doctor": doctor_admin(doctor)})


@admin_bp.patch("/doctors/<int:doctor_id>")
@jwt_required()
@role_required("admin")
def patch_doctor(doctor_id: int):
    doctor = db.session.get(Doctor, doctor_id)
    if not doctor:
        return err("Doctor not found", status_code=404)

    try:
        payload = json_body()
        if "name" in payload:
            doctor.name = payload["name"].strip()
        if "department_id" in payload:
            doctor.department_id = payload["department_id"]
        if "license_number" in payload:
            doctor.license_number = payload["license_number"]
        if "contact_number" in payload:
            doctor.contact_number = payload["contact_number"]
        if "years_experience" in payload:
            doctor.years_experience = parse_years_experience(payload["years_experience"])
        if "bio" in payload:
            doctor.bio = payload["bio"]
        if "is_active" in payload:
            doctor.is_active = bool(payload["is_active"])
        if "password" in payload and payload["password"]:
            doctor.set_password(payload["password"])

        db.session.commit()
        _invalidate_admin_cache()
        return ok({"doctor": doctor_admin(doctor)})
    except ValueError as exc:
        return err(str(exc), status_code=400)


@admin_bp.delete("/doctors/<int:doctor_id>")
@jwt_required()
@role_required("admin")
def delete_doctor(doctor_id: int):
    doctor = db.session.get(Doctor, doctor_id)
    if not doctor:
        return err("Doctor not found", status_code=404)
    doctor.is_active = False
    db.session.commit()
    _invalidate_admin_cache()
    return ok({"msg": "Doctor deactivated"})


# ---------------------------------------------------------------------------
# Patients
# ---------------------------------------------------------------------------


@admin_bp.get("/patients")
@jwt_required()
@role_required("admin")
@cache.cached(timeout=60, query_string=True)
def list_patients():
    q = request.args.get("q", "").strip()
    query = Patient.query
    if q:
        like = f"%{q}%"
        query = query.filter((Patient.name.ilike(like)) | (Patient.email.ilike(like)))
    patients = query.order_by(Patient.created_at.desc()).all()
    return ok({"patients": [patient_admin(p) for p in patients]})


@admin_bp.post("/patients")
@jwt_required()
@role_required("admin")
def create_patient():
    try:
        payload = json_body()
        require_fields(payload, ["email", "password", "name", "dob", "contact_number"])
        email = payload["email"].strip().lower()

        if User.query.filter_by(email=email).first():
            return err("Email already registered", status_code=409)

        patient = Patient(
            email=email,
            name=payload["name"].strip(),
            dob=parse_date(payload["dob"]),
            blood_group=payload.get("blood_group"),
            gender=normalize_gender(payload.get("gender")),
            past_medical_history=payload.get("past_medical_history"),
            contact_number=payload["contact_number"].strip(),
            emergency_contact=payload.get("emergency_contact"),
            address=payload.get("address"),
            is_active=bool(payload.get("is_active", True)),
        )
        patient.set_password(payload["password"])
        db.session.add(patient)
        db.session.commit()
        _invalidate_admin_cache()
        return ok({"patient": patient_admin(patient)}, status_code=201)
    except ValueError as exc:
        return err(str(exc), status_code=400)


@admin_bp.get("/patients/<int:patient_id>")
@jwt_required()
@role_required("admin")
def get_patient(patient_id: int):
    patient = db.session.get(Patient, patient_id)
    if not patient:
        return err("Patient not found", status_code=404)
    return ok({"patient": patient_admin(patient)})


@admin_bp.patch("/patients/<int:patient_id>")
@jwt_required()
@role_required("admin")
def patch_patient(patient_id: int):
    patient = db.session.get(Patient, patient_id)
    if not patient:
        return err("Patient not found", status_code=404)

    try:
        payload = json_body()
        if "name" in payload:
            patient.name = payload["name"].strip()
        if "dob" in payload:
            patient.dob = parse_date(payload["dob"])
        if "blood_group" in payload:
            patient.blood_group = payload["blood_group"]
        if "gender" in payload:
            patient.gender = normalize_gender(payload["gender"])
        if "past_medical_history" in payload:
            patient.past_medical_history = payload["past_medical_history"]
        if "contact_number" in payload:
            patient.contact_number = payload["contact_number"].strip()
        if "emergency_contact" in payload:
            patient.emergency_contact = payload["emergency_contact"]
        if "address" in payload:
            patient.address = payload["address"]
        if "is_active" in payload:
            patient.is_active = bool(payload["is_active"])
        if "password" in payload and payload["password"]:
            patient.set_password(payload["password"])

        db.session.commit()
        _invalidate_admin_cache()
        return ok({"patient": patient_admin(patient)})
    except ValueError as exc:
        return err(str(exc), status_code=400)


@admin_bp.delete("/patients/<int:patient_id>")
@jwt_required()
@role_required("admin")
def delete_patient(patient_id: int):
    patient = db.session.get(Patient, patient_id)
    if not patient:
        return err("Patient not found", status_code=404)
    patient.is_active = False
    db.session.commit()
    _invalidate_admin_cache()
    return ok({"msg": "Patient deactivated"})
