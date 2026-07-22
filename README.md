# LMS Subscription Analytics Platform

A multi-panel backend project built for the three attached tasks:

- Learning Management Platform
- Subscription-Based Video Learning Platform
- Analytics Dashboard and Notification System

The project uses Django for the admin panel, FastAPI for the user panel API, and one shared PostgreSQL database.

## Project Structure

```text
subscription-video-platform/
|-- admin_panel/          Django admin panel, templates, migrations, media, static files
|-- user_api/             FastAPI user panel, routers, services, schemas, SQLAlchemy models
|-- database/             SQL schema and portable dump reference
|-- postman/              Complete Postman collection
|-- screenshots/          Screenshot guidance for final submission
|-- docker-compose.yml    Local development stack
|-- docker-compose.prod.yml
|-- README.md
```

## Features

### Django Admin Panel

- Admin login/logout with Django authentication
- Dashboard cards for users, instructors, courses, lessons, and enrollments
- User and instructor CRUD
- Course and lesson CRUD, including thumbnails, videos, notes, and resources
- Subscription plan management
- User subscription and payment reporting
- Analytics dashboard with user count, active subscriptions, monthly revenue, popular courses, and activity trends
- Notification center for in-app/email notification records
- Django Admin registration for all shared models

### FastAPI User Panel

- JWT registration and login
- Student and instructor roles
- Course browsing and details
- Instructor course and lesson management
- Course enrollment and progress tracking
- Subscription plan listing and purchase
- Premium course access control based on active plan validity
- Payment history and simulated payment creation
- Automatic GST invoice generation with downloadable PDF invoices
- Automatic SMTP email delivery for notifications and invoice PDFs when mail credentials are configured
- Activity logging endpoint and automatic activity logs for enrollments, progress, subscriptions, payments, and course updates
- Notification listing and mark-read endpoint
- Admin analytics APIs
- Consistent error responses and validation

## Shared Database Models

- User
- Course
- Lesson
- Enrollment
- Progress
- Plan
- Subscription
- Payment
- Notification
- ActivityLog
- AnalyticsRecord

## FastAPI Endpoints

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/register/` | Register user |
| POST | `/login/` | Login and return JWT |
| POST | `/auth/register/` | Namespaced register alias |
| POST | `/auth/login/` | Namespaced login alias |

### LMS

| Method | Endpoint | Description |
|---|---|---|
| GET | `/courses/` | List accessible courses |
| GET | `/courses/{course_id}` | Course details |
| POST | `/courses/` | Instructor creates course |
| PUT | `/courses/{course_id}` | Instructor updates course |
| DELETE | `/courses/{course_id}` | Instructor deletes course |
| POST | `/courses/{course_id}/lessons/` | Instructor adds lesson |
| POST | `/enroll/` | Enroll in course |
| GET | `/my-courses/` | View enrolled courses |
| POST | `/progress/update/` | Update course progress |
| GET | `/progress/view/` | View progress |

### Subscriptions and Payments

| Method | Endpoint | Description |
|---|---|---|
| GET | `/plans/` | List active plans |
| GET | `/plans/{plan_id}` | Plan details |
| POST | `/subscribe/` | Purchase a plan with `{ "plan_id": 1 }` |
| POST | `/subscriptions/subscribe/{plan_id}` | Existing subscription route |
| GET | `/subscriptions/me` | Current user's subscriptions |
| POST | `/payments/pay/{subscription_id}` | Create successful payment |
| GET | `/payments/` | Payment history |
| GET | `/payments/history` | Existing payment-history route |
| GET | `/payments/{payment_id}/invoice/` | Download generated invoice PDF |

### Analytics and Notifications

| Method | Endpoint | Description |
|---|---|---|
| GET | `/notifications/` | Fetch current user's notifications |
| POST | `/notifications/mark-read/` | Mark selected or all notifications read |
| POST | `/activity/` | Log user activity |
| GET | `/activity/` | Current user's activity logs |
| GET | `/analytics/overview/` | Admin analytics summary |
| GET | `/analytics/monthly/` | Admin monthly revenue stats |
| GET | `/analytics/revenue-by-plan/` | Admin revenue by plan stats |
| POST | `/notifications/broadcast/` | Admin broadcast notification |

## Docker Setup

```bash
docker compose up --build
```

After the services start:

| Service | URL |
|---|---|
| Django Admin Panel | http://localhost:8000 |
| Django built-in admin | http://localhost:8000/django-admin/ |
| FastAPI Swagger | http://localhost:8001/docs |
| PostgreSQL | localhost:5432 |

Create an admin user:

```bash
docker compose exec admin_panel python manage.py createsuperuser
```

## Manual Setup

### Database

Create a PostgreSQL database and set these variables as needed:

```bash
POSTGRES_DB=lms_db
POSTGRES_USER=lms_user
POSTGRES_PASSWORD=lms_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### Django Admin Panel

```bash
cd admin_panel
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 8000
```

### FastAPI User Panel

```bash
cd user_api
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

## API Testing

Import this file into Postman:

```text
postman/LMS_Platform.postman_collection.json
```

You can also test through Swagger:

```text
http://localhost:8001/docs
```

## Database Deliverables

Recommended source of truth:

```text
admin_panel/*/migrations/
```

Portable SQL reference:

```text
database/schema.sql
database/lms_dump.sql
```

## Submission Notes

- Add screenshots or a short demo video under `screenshots/`.
- Include this repository, the migrations or SQL dump, and the Postman collection in the final submission.
- Celery/Redis is optional in the task document; this implementation keeps notification/activity processing synchronous and database-backed for easy local review.

## Invoice Generation

When a payment is created, the application automatically generates:

- Invoice number, for example `INV-20260717-A1B2C3`
- Transaction ID, for example `TXN-9F8E7D6C5B4A`
- GST-inclusive total amount
- Downloadable subscription invoice PDF matching the required invoice layout

Invoice downloads are available from:

- Django Admin Panel: Payments -> View -> Download Invoice
- FastAPI: `GET /payments/{payment_id}/invoice/`

## Auto Email Generation

The FastAPI service automatically tries to send emails for:

- Subscription purchase notifications
- Course enrollment notifications
- Course and lesson update notifications
- Course completion notifications
- Payment success invoice emails with the generated PDF attached

Set these environment variables in `.env`, Docker, or your deployment platform:

```bash
DEFAULT_FROM_EMAIL=your-email@example.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=True
```

If SMTP details are missing, the app still creates in-app notifications and keeps running. Email delivery is skipped safely until credentials are added.
## Production Student Portal

The student side now behaves like a real LMS user application:

- Django renders student templates and static assets.
- FastAPI handles JWT authentication and business APIs.
- Students can register, login, browse courses, enroll, continue learning, track progress, subscribe to plans, pay, download invoices, view notifications, and manage profile details.
- Students cannot access admin analytics, user management, plan management, or payment management.

Student URLs:

```text
/student/
/student/register/
/student/dashboard/
/student/courses/
/student/course/<id>/
/student/my-courses/
/student/lesson/<id>/
/student/plans/
/student/subscription/
/student/payments/
/student/notifications/
/student/chat/

### Production-style messaging

- Student-to-instructor messages are delivered immediately over WebSockets while users have an LMS page open.
- Conversations and messages show participant names instead of database user numbers.
- Presence includes online, offline, and last-seen states.
- One tick means sent, two grey ticks mean delivered, and two blue ticks mean read.
- Message notifications arrive on every authenticated student or instructor page through the notification WebSocket.
- Private conversation creation reuses an existing participant conversation to avoid duplicate threads.
- Historical messages are backfilled as delivered/read by analytics migration `0006_backfill_chat_message_receipts.py`.

After pulling this messaging update, run:

```bash
docker compose exec admin_panel python manage.py migrate
docker compose restart admin_panel user_api
```
/student/assignments/
/student/attendance/
/student/profile/
```

FastAPI base URL for the Django-rendered student frontend is controlled by:

```text
FASTAPI_BASE_URL=http://localhost:8001
```

See `STUDENT_MODULE_PRODUCTION_REPORT.md` for modified files, API mapping, restrictions, and validation notes.

## Instructor Portal

The instructor workspace is separate from both the student portal and Django administration:

```text
/instructor/             Instructor-only login
/instructor/dashboard/  Courses, learners, assignments, grading, attendance, notifications
```

Role checks are enforced by both the frontend and FastAPI. Students cannot enter the instructor workspace, and instructor accounts are rejected by the student login. Public registration always creates a student; instructor accounts must be approved by an administrator.

All application accounts use Gmail-format addresses. Demo Gmail accounts are local test identities unless you configure SMTP and own the corresponding mailboxes.

### Updating an older Docker copy

The Compose services use project-scoped names instead of fixed global container names. If an older copy is already running, recreate the services once:

```bash
docker compose down
docker compose up --build -d
```

Do not add `-v` to `docker compose down` unless you intentionally want to erase PostgreSQL and Redis data. Deleting a ZIP file never deletes Docker containers or named volumes.

## Advanced LMS Module (Day 4)

The existing shared-database application now also includes:

- Attendance marking and reporting with instructor ownership, enrollment checks, date ranges, percentage calculation, and duplicate protection.
- Assignment creation, secure 10 MB file upload, enrolled-student submission, deadline enforcement, duplicate prevention, grading, and notification triggers.
- Django JSON analytics at `GET /analytics/dashboard/?course_id=<id>`.
- Student portal pages at `/student/assignments/` and `/student/attendance/`.
- Mirrored Django and SQLAlchemy models backed by migration `courses/0005_attendance_assignment_submission.py`.

FastAPI endpoints:

```text
POST /attendance/mark
GET  /attendance/student/{student_id}/?course_id={course_id}
GET  /attendance/course/{course_id}/?from=YYYY-MM-DD&to=YYYY-MM-DD
GET  /assignments/
POST /assignments/create
POST /assignments/submit
GET  /assignments/submissions/
PUT  /assignments/grade
```

### Realistic demo data

After the containers are healthy, create idempotent demo data:

```bash
docker compose exec -e SEED_DEMO_PASSWORD='DemoPass123!' admin_panel python manage.py seed_demo
```

This creates an admin, instructor, three students, three published courses with lessons, Basic/Pro/Enterprise plans, active subscriptions, enrollments, progress, attendance, an assignment, and a graded submission. Change the password outside local demonstrations.

| Role | Email | Local demo password |
|---|---|---|
| Admin | `khaja.admin@gmail.com` | value of `SEED_DEMO_PASSWORD` |
| Instructor | `ravi.instructor@gmail.com` | value of `SEED_DEMO_PASSWORD` |
| Student | `khaja1@gmail.com` | value of `SEED_DEMO_PASSWORD` |
| Student | `meera.sharma1@gmail.com` | value of `SEED_DEMO_PASSWORD` |
| Student | `arjun.reddy1@gmail.com` | value of `SEED_DEMO_PASSWORD` |

### Final Docker verification

```bash
docker compose config --quiet
docker compose up --build -d
docker compose exec admin_panel python manage.py migrate --check
docker compose exec admin_panel python manage.py check --deploy
curl http://localhost:8001/
```
