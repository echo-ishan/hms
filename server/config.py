import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
    APP_TIMEZONE = os.environ.get("APP_TIMEZONE", "Asia/Kolkata")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'hms.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    _db_uri = SQLALCHEMY_DATABASE_URI or ""
    if _db_uri.startswith("sqlite:"):
        SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"timeout": 30}}
    else:
        # psycopg2 uses `connect_timeout` (seconds); `timeout` is not a valid option for Postgres DSNs.
        SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"connect_timeout": 30}}

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "jwt-dev-secret-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ["headers", "cookies"]
    JWT_COOKIE_SAMESITE = os.environ.get("JWT_COOKIE_SAMESITE", "Lax")
    JWT_COOKIE_CSRF_PROTECT = True
    JWT_CSRF_IN_COOKIES = True
    JWT_COOKIE_SECURE = os.environ.get("JWT_COOKIE_SECURE", "0") not in ("0", "false", "False")

    # Comma-separated list of allowed origins. Example:
    # CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://your-custom-domain.com
    CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "")

    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    CACHE_TYPE = os.environ.get("CACHE_TYPE", "RedisCache")
    CACHE_REDIS_URL = os.environ.get("CACHE_REDIS_URL", REDIS_URL)
    CACHE_DEFAULT_TIMEOUT = int(os.environ.get("CACHE_DEFAULT_TIMEOUT", "300"))

    CELERY = {
        "broker_url": os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1"),
        "result_backend": os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
        "task_ignore_result": False,
    }

    DAILY_REMINDER_HOUR = int(os.environ.get("DAILY_REMINDER_HOUR", "2"))
    DAILY_REMINDER_MINUTE = int(os.environ.get("DAILY_REMINDER_MINUTE", "4"))
    MONTHLY_REPORT_HOUR = int(os.environ.get("MONTHLY_REPORT_HOUR", "9"))
    MONTHLY_REPORT_MINUTE = int(os.environ.get("MONTHLY_REPORT_MINUTE", "0"))

    SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 1025))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM = os.environ.get("SMTP_FROM", "hms@example.com")

    # Mailpit defaults (dev): host=localhost port=1025 user/pass empty
    SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "0") not in ("0", "false", "False")

    # Email delivery mode:
    # - smtp (default): deliver via SMTP settings above
    # - log: don't send; log the email payload (good for public demos w/o credentials)
    EMAIL_MODE = os.environ.get("EMAIL_MODE", "smtp").lower()
