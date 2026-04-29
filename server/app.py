import logging
import os

from flask import Flask
from flask import jsonify, request

from celery_app import create_celery
from config import Config
from extensions import cache, db, jwt

logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    logging.basicConfig(level=logging.INFO)
    flask_app = Flask(__name__, instance_relative_config=True)
    flask_app.config.from_object(config_class)

    os.makedirs(flask_app.instance_path, exist_ok=True)

    db.init_app(flask_app)
    jwt.init_app(flask_app)
    cache.init_app(flask_app)

    flask_app.extensions["celery"] = create_celery(flask_app)

    _register_blueprints(flask_app)
    _configure_jwt_callbacks()
    _register_error_handlers(flask_app)
    _register_options_handler(flask_app)
    _add_cors_headers(flask_app)

    with flask_app.app_context():
        import models  # noqa: F401 — registers all models with SQLAlchemy
        db.create_all()
        _seed_data()

    return flask_app


def _register_blueprints(flask_app):
    from controllers import auth_bp, admin_bp, doctor_bp, patient_bp
    import controllers.auth  # noqa: F401
    import controllers.admin  # noqa: F401
    import controllers.doctor  # noqa: F401
    import controllers.patient  # noqa: F401

    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(admin_bp)
    flask_app.register_blueprint(doctor_bp)
    flask_app.register_blueprint(patient_bp)


def _configure_jwt_callbacks():
    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        from models import User
        try:
            user_id = int(identity)
        except (TypeError, ValueError):
            return {"role": None}

        user = db.session.get(User, user_id)
        return {"role": user.type if user else None}

    @jwt.user_identity_loader
    def user_identity_lookup(user_id):
        return user_id

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        from models import User
        identity = jwt_data["sub"]
        try:
            user_id = int(identity)
        except (TypeError, ValueError):
            return None
        return db.session.get(User, user_id)


def _register_error_handlers(flask_app):
    @flask_app.errorhandler(404)
    def not_found(_error):
        return jsonify(msg="Not found"), 404

    @flask_app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify(msg="Method not allowed"), 405

    @flask_app.errorhandler(400)
    def bad_request(_error):
        return jsonify(msg="Bad request"), 400

    @flask_app.errorhandler(500)
    def server_error(_error):
        return jsonify(msg="Internal server error"), 500


def _register_options_handler(flask_app):
    @flask_app.before_request
    def handle_options_requests():
        if request.method == "OPTIONS":
            return ("", 200)


def _add_cors_headers(flask_app):
    allowed_origins = {"http://localhost:5173", "http://127.0.0.1:5173"}
    extra_origins = flask_app.config.get("CORS_ALLOWED_ORIGINS", "")
    if extra_origins:
        for origin in extra_origins.split(","):
            origin = origin.strip()
            if origin:
                allowed_origins.add(origin)

    @flask_app.after_request
    def cors(response):
        origin = request.headers.get("Origin")
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-CSRF-TOKEN"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response


def _seed_data():
    from models import Admin, Department

    if not Admin.query.first():
        admin = Admin(email="admin@hms.com", is_active=True)
        admin.set_password("Admin@123")
        db.session.add(admin)
        logger.info("Admin seeded successfully: %s", admin.email)
    else:
        logger.info("Admin already exists; skipping seed.")

    default_departments = [
        ("General Medicine", "Primary care and internal medicine"),
        ("Cardiology", "Heart and cardiovascular system"),
        ("Orthopedics", "Bones, joints, and musculoskeletal system"),
        ("Pediatrics", "Medical care for infants, children, and adolescents"),
        ("Dermatology", "Skin, hair, and nail conditions"),
        ("Neurology", "Brain, spinal cord, and nervous system"),
        ("Ophthalmology", "Eye care and vision"),
        ("ENT", "Ear, nose, and throat"),
        ("Gynecology", "Women's reproductive health"),
        ("Psychiatry", "Mental health and behavioral disorders"),
    ]

    for name, description in default_departments:
        if not Department.query.filter_by(name=name).first():
            db.session.add(Department(name=name, description=description))

    db.session.commit()


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
