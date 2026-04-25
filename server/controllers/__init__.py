from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")
doctor_bp = Blueprint("doctor", __name__, url_prefix="/api/doctor")
patient_bp = Blueprint("patient", __name__, url_prefix="/api/patient")
