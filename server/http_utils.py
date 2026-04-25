from __future__ import annotations

from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from flask import current_app, jsonify, request


def json_body() -> dict:
    if not request.is_json:
        raise ValueError("Expected application/json body")
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        raise ValueError("Invalid JSON body")
    return payload


def ok(data: dict | list | None = None, *, status_code: int = 200):
    if data is None:
        data = {}
    return jsonify(data), status_code


def err(message: str, *, status_code: int = 400, **extra):
    payload = {"msg": message}
    if extra:
        payload.update(extra)
    return jsonify(payload), status_code


def require_fields(payload: dict, fields: list[str]) -> None:
    missing = [field for field in fields if payload.get(field) in (None, "")]
    if missing:
        raise ValueError(f"Missing fields: {', '.join(missing)}")


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Invalid date; expected YYYY-MM-DD") from exc


def parse_time(value: str) -> time:
    try:
        return time.fromisoformat(value)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Invalid time; expected HH:MM[:SS]") from exc


def parse_datetime(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Invalid datetime; expected ISO 8601") from exc

    tz = ZoneInfo(current_app.config.get("APP_TIMEZONE", "Asia/Kolkata"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(tz).replace(tzinfo=None)


def normalize_gender(value) -> str | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ValueError("Invalid gender; expected Male, Female, or Other")

    mapping = {
        "male": "Male",
        "female": "Female",
        "other": "Other",
    }
    normalized = mapping.get(value.strip().lower())
    if not normalized:
        raise ValueError("Invalid gender; expected Male, Female, or Other")
    return normalized


def parse_years_experience(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        years = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid years_experience; expected an integer between 0 and 80") from exc

    if years < 0 or years > 80:
        raise ValueError("Invalid years_experience; expected an integer between 0 and 80")
    return years
