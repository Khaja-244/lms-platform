# AKR LMS - Production Submission Report

## Scope

This repository combines all four supplied assignments in one shared PostgreSQL project:

1. Django admin + FastAPI learner/instructor LMS.
2. Subscription-based video learning and payment history.
3. Real-time private/group chat, file sharing, presence, notifications, and chat analytics.
4. Attendance, assignments, submissions, grading, notifications, and course analytics.

## Implemented frontend

The Django-rendered portal consumes the FastAPI API with JWT authentication and includes dashboard, courses, enrollment, lessons, progress, plans, subscription, payments, invoices, notifications, profile, live chat, assignments, grading, and attendance workflows. Role-aware controls expose instructor actions only to instructors/admins; the API remains the authoritative authorization layer.

## Production blockers corrected

- Removed a committed runtime `.env` and replaced exposed SMTP values with placeholders. The original SMTP app password must be revoked/rotated by its owner.
- Added a production startup guard that rejects default JWT secrets.
- Removed unreachable duplicated authentication code.
- Prevented unauthorized chat participant administration and room-owner removal.
- Made chat-room creation atomic and validated active participant IDs/private-room size.
- Removed the Docker startup race by making FastAPI wait for required Django migrations and disabling automatic SQLAlchemy DDL by default.
- Added missing database migration coverage for chat, attendance, assignments, and submissions.
- Added duplicate attendance, enrollment, course ownership, role, deadline, duplicate submission, grade range, filename, extension, and upload-size validation.
- Added assignment/attendance notification triggers and Django ORM analytics.

## Demo data

Run:

```bash
docker compose exec -e SEED_DEMO_PASSWORD='DemoPass123!' admin_panel python manage.py seed_demo
```

The idempotent command creates:

- Admin: `khaja.admin@gmail.com`
- Instructor: `ravi.instructor@gmail.com`
- Students: `khaja1@gmail.com`, `meera.sharma1@gmail.com`, `arjun.reddy1@gmail.com`
- Courses: Django & FastAPI Production Backend; Python Foundations; Real-Time Web Applications
- Plans: Basic, Pro, Enterprise
- Lessons, enrollments, progress, active subscriptions, three days of attendance, an assignment, and a graded submission

All demo accounts use the value supplied through `SEED_DEMO_PASSWORD` and are intended only for local demonstration.

## Included deliverables

- Django and FastAPI source
- Django migrations and `database/schema.sql`
- Main Postman collection plus `LMS_Day4_Advanced_Features.postman_collection.json`
- Docker Compose development and production-overlay configuration
- Safe environment templates
- README setup/API/demo instructions
- Screenshot checklist under `screenshots/`

## Verification performed

- All Python files compiled and parsed successfully.
- All JavaScript files passed Node syntax validation.
- All JSON/Postman files parsed successfully.
- Development Compose and combined production Compose configurations validated successfully.
- `git diff --check` passed.
- Runtime `.env` files were excluded from the submission.
- Archive contents and final ZIP integrity were checked.

Docker Desktop was installed but its Linux engine named pipe was not accessible from the audit task, so a live container build/run could not be completed in this environment. Run the commands below locally before recording screenshots:

```bash
docker compose up --build -d
docker compose exec admin_panel python manage.py migrate --check
docker compose exec admin_panel python manage.py check --deploy
docker compose exec admin_panel python manage.py seed_demo
curl http://localhost:8001/
```
