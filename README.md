# Hospital Management System

A full-stack Hospital Management System for managing patients, doctors, departments, appointments, and treatment records. The project is split into a **Vue 3 + Vite frontend** and a **Flask backend** with JWT authentication, role-based access control, Celery background jobs, and Redis-backed caching.

## Overview

This application is designed for three user roles:

- **Admin** – manages doctors, patients, departments, and appointment operations.
- **Doctor** – manages availability, reviews appointments, and updates visit status.
- **Patient** – registers, browses doctors and departments, books appointments, and exports treatment history.

## Tech Stack

### Frontend
- Vue 3
- Vite
- Pinia for state management
- Bun package manager

### Backend
- Flask
- Flask-JWT-Extended for authentication
- SQLAlchemy for ORM/database access
- Celery for background jobs
- Redis for caching and task broker/result backend

## Features

- Patient self-registration and login
- JWT-based authentication with support for bearer tokens and cookies
- Role-based authorization for admin, doctor, and patient workflows
- Department management
- Doctor profile and availability management
- Appointment booking, cancellation, and status updates
- Admin dashboard with system statistics and management screens
- Background email reminders and scheduled reports
- CSV export of completed treatment history for patients
- Redis-backed response caching
- CORS configured for local Vue development

## Project Structure

```text
hms/
├── frontend/   # Vue 3 + Vite application
├── server/     # Flask API, Celery, models, controllers, and config
└── README.md   # Project documentation
```

## Prerequisites

Before running the project, make sure you have:

- **Bun** installed for the frontend
- **Python** and the backend dependencies available
- **Redis** running locally
- **Mailpit** or another SMTP server for email testing in development

## Local Development Setup

### 1) Backend

From the `server` directory:

```sh
./setup.sh
./run.sh
```

The backend runs at:

```text
http://127.0.0.1:5000
```

#### Default seeded data

On startup, the backend seeds:

- an admin user: `admin@hms.com` / `Admin@123`
- default departments such as Cardiology, Orthopedics, Pediatrics, Dermatology, and more

### 2) Frontend

From the `frontend` directory:

```sh
bun install
bun dev
```

The frontend development server will start on the default Vite port.

## Authentication

The API uses JWT authentication. Tokens can be sent in either of these ways:

- `Authorization: Bearer <token>` header
- secure cookies

Recommended frontend flow:

1. Store the access token in memory, such as Pinia.
2. Send the access token using the `Authorization` header.
3. Use the refresh token stored in an HttpOnly cookie to rotate access tokens via `POST /api/auth/refresh`.

## API Endpoints

### Auth
- `POST /api/auth/register` — patient self-registration
- `POST /api/auth/login`
- `POST /api/auth/refresh`
- `POST /api/auth/logout`
- `GET /api/auth/me`

### Admin
- `GET /api/admin/stats`
- `GET /api/admin/appointments`
- `PATCH /api/admin/appointments/<appointment_id>` — cancel booked appointment
- `GET /api/admin/departments`
- `POST /api/admin/departments`
- `GET /api/admin/doctors`
- `POST /api/admin/doctors`
- `GET /api/admin/doctors/<doctor_id>`
- `PATCH /api/admin/doctors/<doctor_id>`
- `DELETE /api/admin/doctors/<doctor_id>`
- `GET /api/admin/patients`
- `POST /api/admin/patients`
- `GET /api/admin/patients/<patient_id>`
- `PATCH /api/admin/patients/<patient_id>`
- `DELETE /api/admin/patients/<patient_id>`

### Doctor
- `GET /api/doctor/me`
- `GET /api/doctor/availability`
- `POST /api/doctor/availability`
- `DELETE /api/doctor/availability/<slot_id>`
- `GET /api/doctor/appointments`
- `PATCH /api/doctor/appointments/<appointment_id>`

### Patient
- `GET /api/patient/me`
- `GET /api/patient/departments`
- `GET /api/patient/doctors`
- `GET /api/patient/doctors/<doctor_id>`
- `GET /api/patient/doctors/<doctor_id>/availability`
- `GET /api/patient/appointments`
- `POST /api/patient/appointments`
- `PATCH /api/patient/appointments/<appointment_id>` — cancel only
- `POST /api/patient/exports/treatments` — async CSV export of completed treatments
- `GET /api/patient/exports/<task_id>` — poll export status

## Background Jobs

The backend uses Celery for scheduled and async work.

### Worker
```sh
cd server && uv run celery -A worker.celery worker -l info
```

### Beat scheduler
```sh
cd server && uv run celery -A worker.celery beat -l info
```

### Scheduled tasks
- Daily reminder emails for patients with booked appointments for today
- Monthly doctor activity report on day 1 for the previous month
- Async CSV export for patient treatment history

## Redis Configuration

Redis is used for:

- Celery broker
- Celery result backend
- Flask-Caching response cache

Default environment values:

```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CACHE_TYPE=RedisCache
CACHE_REDIS_URL=redis://localhost:6379/0
```

## Email Development Setup

For local email testing, configure:

```env
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USE_TLS=0
```

### Mailpit quick start

```sh
brew install mailpit
mailpit
```

- SMTP server: `localhost:1025`
- Web UI: `http://127.0.0.1:8025`

## Deployment Notes

If you are deploying to a platform that does not support separate background workers on a free tier, the project includes a combined startup approach for running the API and Celery processes together.

## Development Notes

- The backend automatically creates the database schema on startup.
- CORS is configured for local frontend origins such as `http://localhost:5173` and `http://127.0.0.1:5173`.
- The application includes default error handlers for common API failures such as 400, 404, 405, and 500.

## Contributing

If you plan to extend the project, good next steps include:

- adding automated tests
- documenting environment variables in a `.env.example`
- adding Swagger/OpenAPI docs
- improving role-specific UI flows in the frontend

