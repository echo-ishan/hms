from __future__ import annotations

from models import Appointment, Department, Doctor, DoctorAvailability, Patient, User


def user_base(user: User) -> dict:
    return user.to_dict()


def department_public(dept: Department) -> dict:
    return {
        "id": dept.id,
        "name": dept.name,
        "description": dept.description,
    }


def department_admin(dept: Department) -> dict:
    payload = department_public(dept)
    payload["doctor_count"] = dept.doctors.count()
    return payload


def doctor_public(doctor: Doctor) -> dict:
    payload = doctor.to_dict()
    payload["department_name"] = doctor.department.name if doctor.department else None
    return payload


def doctor_admin(doctor: Doctor) -> dict:
    payload = doctor_public(doctor)
    payload["department_name"] = doctor.department.name if doctor.department else None
    return payload


def patient_public(patient: Patient) -> dict:
    return patient.to_dict()


def patient_admin(patient: Patient) -> dict:
    return patient_public(patient)


def availability_slot(slot: DoctorAvailability) -> dict:
    return slot.to_dict()


def appointment_doctor_view(appt: Appointment) -> dict:
    payload = appt.to_dict()
    payload["patient_name"] = appt.patient.name if appt.patient else None
    payload["patient_dob"] = appt.patient.dob.isoformat() if appt.patient and appt.patient.dob else None
    payload["patient_gender"] = appt.patient.gender if appt.patient else None
    payload["patient_blood_group"] = appt.patient.blood_group if appt.patient else None
    payload["patient_contact_number"] = appt.patient.contact_number if appt.patient else None
    payload["patient_emergency_contact"] = appt.patient.emergency_contact if appt.patient else None
    payload["patient_address"] = appt.patient.address if appt.patient else None
    payload["patient_past_medical_history"] = appt.patient.past_medical_history if appt.patient else None
    return payload


def appointment_patient_view(appt: Appointment) -> dict:
    payload = appt.to_dict()
    payload["doctor_name"] = appt.doctor.name if appt.doctor else None
    return payload


def appointment_admin_view(appt: Appointment) -> dict:
    payload = appt.to_dict()
    payload["doctor_name"] = appt.doctor.name if appt.doctor else None
    payload["patient_name"] = appt.patient.name if appt.patient else None
    return payload


def appointment_patient_history_view(appt: Appointment) -> dict:
    payload = appt.to_dict()
    payload["doctor_name"] = appt.doctor.name if appt.doctor else None
    payload["department_name"] = appt.doctor.department.name if appt.doctor and appt.doctor.department else None
    payload["patient_name"] = appt.patient.name if appt.patient else None
    return payload

