from datetime import datetime, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from extensions import db

_ph = PasswordHasher()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "user",
    }

    def set_password(self, password):
        self.password_hash = _ph.hash(password)

    def check_password(self, password):
        try:
            return _ph.verify(self.password_hash, password)
        except VerifyMismatchError:
            return False

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "type": self.type,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Admin(User):
    __tablename__ = "admins"

    id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "admin"}


class Doctor(User):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    license_number = db.Column(db.String(50), unique=True, nullable=True)
    contact_number = db.Column(db.String(20), nullable=True)
    years_experience = db.Column(db.Integer, nullable=True)
    bio = db.Column(db.Text, nullable=True)

    appointments = db.relationship("Appointment", back_populates="doctor", lazy="dynamic")
    availability_slots = db.relationship(
        "DoctorAvailability", back_populates="doctor", lazy="dynamic", cascade="all, delete-orphan"
    )

    __mapper_args__ = {"polymorphic_identity": "doctor"}

    def to_dict(self):
        base = super().to_dict()
        base.update({
            "name": self.name,
            "department_id": self.department_id,
            "license_number": self.license_number,
            "contact_number": self.contact_number,
            "years_experience": self.years_experience,
            "bio": self.bio,
        })
        return base


class Patient(User):
    __tablename__ = "patients"

    id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    blood_group = db.Column(db.String(5), nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    past_medical_history = db.Column(db.Text, nullable=True)
    contact_number = db.Column(db.String(20), nullable=False)
    emergency_contact = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)

    appointments = db.relationship("Appointment", back_populates="patient", lazy="dynamic")

    __mapper_args__ = {"polymorphic_identity": "patient"}

    def to_dict(self):
        base = super().to_dict()
        base.update({
            "name": self.name,
            "dob": self.dob.isoformat() if self.dob else None,
            "blood_group": self.blood_group,
            "gender": self.gender,
            "past_medical_history": self.past_medical_history,
            "contact_number": self.contact_number,
            "emergency_contact": self.emergency_contact,
            "address": self.address,
        })
        return base


# ---------------------------------------------------------------------------
# Department
# ---------------------------------------------------------------------------

class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)

    doctors = db.relationship("Doctor", backref="department", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
        }


# ---------------------------------------------------------------------------
# Appointment (with merged treatment fields)
# ---------------------------------------------------------------------------

class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False, index=True)
    start_time = db.Column(db.DateTime, nullable=False, index=True)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="booked")
    visit_reason = db.Column(db.String(255), nullable=True)

    # Treatment fields — filled by doctor upon completion
    diagnosis = db.Column(db.Text, nullable=True)
    prescription = db.Column(db.Text, nullable=True)
    tests_requested = db.Column(db.Text, nullable=True)
    medications_prescribed = db.Column(db.Text, nullable=True)
    follow_up_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint("doctor_id", "start_time", name="uq_doctor_timeslot"),
    )

    doctor = db.relationship("Doctor", back_populates="appointments")
    patient = db.relationship("Patient", back_populates="appointments")

    VALID_STATUSES = {"booked", "completed", "cancelled"}
    VALID_TRANSITIONS = {
        "booked": {"completed", "cancelled"},
        "completed": set(),
        "cancelled": set(),
    }

    def can_transition_to(self, new_status):
        return new_status in self.VALID_TRANSITIONS.get(self.status, set())

    def to_dict(self):
        return {
            "id": self.id,
            "doctor_id": self.doctor_id,
            "patient_id": self.patient_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "visit_reason": self.visit_reason,
            "diagnosis": self.diagnosis,
            "prescription": self.prescription,
            "tests_requested": self.tests_requested,
            "medications_prescribed": self.medications_prescribed,
            "follow_up_date": self.follow_up_date.isoformat() if self.follow_up_date else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ---------------------------------------------------------------------------
# Doctor Availability
# ---------------------------------------------------------------------------

class DoctorAvailability(db.Model):
    __tablename__ = "doctor_availability"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("doctor_id", "date", "start_time", name="uq_doctor_date_slot"),
    )

    doctor = db.relationship("Doctor", back_populates="availability_slots")

    def to_dict(self):
        return {
            "id": self.id,
            "doctor_id": self.doctor_id,
            "date": self.date.isoformat() if self.date else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }
