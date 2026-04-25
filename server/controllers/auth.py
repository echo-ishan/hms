from datetime import datetime, timezone

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    get_csrf_token,
    jwt_required,
    set_refresh_cookies,
    unset_jwt_cookies,
)

from controllers import auth_bp
from extensions import db
from http_utils import err, json_body, normalize_gender, ok, parse_date, require_fields
from models import Patient, User
from serializers import patient_public, user_base


@auth_bp.post("/register")
def register_patient():
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
            is_active=True,
        )
        patient.set_password(payload["password"])
        db.session.add(patient)
        db.session.commit()

        return ok({"user": patient_public(patient)}, status_code=201)
    except ValueError as exc:
        return err(str(exc), status_code=400)


@auth_bp.post("/login")
def login():
    try:
        payload = json_body()
        require_fields(payload, ["email", "password"])

        email = payload["email"].strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(payload["password"]):
            return err("Invalid credentials", status_code=401)
        if not user.is_active:
            return err("Account is disabled", status_code=403)

        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        refresh_csrf = get_csrf_token(refresh_token)

        response, _ = ok(
            {"access_token": access_token, "refresh_csrf": refresh_csrf, "user": user_base(user)}
        )
        set_refresh_cookies(response, refresh_token)
        return response, 200
    except ValueError as exc:
        return err(str(exc), status_code=400)


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        return err("Invalid token subject", status_code=401)

    user = db.session.get(User, user_id_int)
    if not user or not user.is_active:
        return err("Invalid user", status_code=401)

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    refresh_csrf = get_csrf_token(refresh_token)
    response, _ = ok({"access_token": access_token, "refresh_csrf": refresh_csrf, "user": user_base(user)})
    set_refresh_cookies(response, refresh_token)
    return response, 200


@auth_bp.post("/logout")
def logout():
    response, _ = ok({"msg": "Logged out"})
    unset_jwt_cookies(response)
    return response, 200


@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        return err("Invalid token subject", status_code=401)

    user = db.session.get(User, user_id_int)
    if not user:
        return err("User not found", status_code=404)
    return ok({"user": user_base(user), "server_time": datetime.now(timezone.utc).isoformat()})
