# HMS Backend (Flask)

## Run locally

- Install + create DB: `./setup.sh`
- Start API server: `./run.sh`
- API base URL: `http://127.0.0.1:5000`

The app seeds:
- an admin user: `admin@hms.com` / `Admin@123`
- default departments (see `server/app.py`)

## Auth

JWT is accepted via `Authorization: Bearer <token>` **or** cookies.

Recommended for Vue/Pinia:
- Store access token in memory (Pinia) and send it via `Authorization` header.
- Use refresh token (HttpOnly cookie) with `POST /api/auth/refresh` to rotate access tokens.

### Endpoints

- `POST /api/auth/register` (patient self-register)
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`

## Admin (role: `admin`)

- `GET /api/admin/stats`
- `GET /api/admin/appointments`
- `PATCH /api/admin/appointments/<appointment_id>` (cancel booked appointment)
- `GET/POST /api/admin/departments`
- `GET/POST /api/admin/doctors`
- `GET/PATCH/DELETE /api/admin/doctors/<doctor_id>`
- `GET/POST /api/admin/patients`
- `GET/PATCH/DELETE /api/admin/patients/<patient_id>`

## Doctor (role: `doctor`)

- `GET /api/doctor/me`
- `GET/POST /api/doctor/availability`
- `DELETE /api/doctor/availability/<slot_id>`
- `GET /api/doctor/appointments`
- `PATCH /api/doctor/appointments/<appointment_id>`

## Patient (role: `patient`)

- `GET /api/patient/me`
- `GET /api/patient/departments`
- `GET /api/patient/doctors`
- `GET /api/patient/doctors/<doctor_id>`
- `GET /api/patient/doctors/<doctor_id>/availability`
- `GET/POST /api/patient/appointments`
- `PATCH /api/patient/appointments/<appointment_id>` (cancel only)
- `POST /api/patient/exports/treatments` (async CSV export of completed treatments)
- `GET /api/patient/exports/<task_id>` (poll export status)

## Celery

- Worker: `cd server && uv run celery -A worker.celery worker -l info`
- Beat (scheduler): `cd server && uv run celery -A worker.celery beat -l info`

Periodic tasks are wired in `server/celery_app.py:1`.

Configured jobs:
- Daily reminder email to patients with booked appointments for today.
- Monthly doctor activity report on day 1 (for the previous month's completed visits).
- Patient-triggered CSV export of completed treatment history.

## Redis + Caching

The backend uses Redis for:
- Celery broker and result backend
- Flask-Caching response cache

Defaults:
- `REDIS_URL=redis://localhost:6379/0`
- `CELERY_BROKER_URL=redis://localhost:6379/1`
- `CELERY_RESULT_BACKEND=redis://localhost:6379/1`
- `CACHE_TYPE=RedisCache`
- `CACHE_REDIS_URL=redis://localhost:6379/0`

## Email (Mailpit for dev)

Set these env vars before running server/worker:
- `SMTP_HOST=localhost`
- `SMTP_PORT=1025`
- `SMTP_USE_TLS=0`

Mailpit quick start (macOS/Homebrew):
- `brew install mailpit`
- `mailpit`
- SMTP server: `localhost:1025`
- Web UI: `http://127.0.0.1:8025`
