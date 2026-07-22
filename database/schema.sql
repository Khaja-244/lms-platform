-- ============================================================================
-- LMS Platform - Database Schema
-- ============================================================================
-- This file is a REFERENCE copy of the schema that Django's migrations
-- create automatically. You do NOT need to run this file if you use
-- `python manage.py migrate` (recommended) - it's provided for:
--   - reviewers who want to see the schema without running Django
--   - manually inspecting/recreating the DB
--   - the "Database schema (SQL dump)" deliverable requested in the task
--
-- NOTE: Django also creates its own internal bookkeeping tables
-- (django_migrations, django_session, django_content_type,
-- auth_permission, accounts_user_groups, accounts_user_user_permissions,
-- django_admin_log). These are used only by Django itself (sessions,
-- the built-in /django-admin/ permission system) - FastAPI never reads
-- or writes them, so they're intentionally left out below. The shared
-- project tables from the LMS, subscription, analytics, and notification
-- tasks are listed here.
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(150) NOT NULL,
    email           VARCHAR(254) UNIQUE NOT NULL,
    role            VARCHAR(20) NOT NULL DEFAULT 'student',   -- admin | instructor | student
    profile_picture TEXT NOT NULL DEFAULT '',
    password_hash   VARCHAR(128) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_staff        BOOLEAN NOT NULL DEFAULT FALSE,
    is_superuser    BOOLEAN NOT NULL DEFAULT FALSE,
    last_login      TIMESTAMPTZ,
    date_joined     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS courses (
    id              BIGSERIAL PRIMARY KEY,
    title           VARCHAR(200) NOT NULL,
    description     TEXT DEFAULT '',
    thumbnail       VARCHAR(255),
    duration        VARCHAR(100) NOT NULL DEFAULT '0 Hours',
    level           VARCHAR(30) NOT NULL DEFAULT 'Beginner',
    instructor_id   BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status          VARCHAR(20) NOT NULL DEFAULT 'draft',      -- draft | published | archived
    is_premium      BOOLEAN NOT NULL DEFAULT FALSE,
    price           NUMERIC(10, 2) NOT NULL DEFAULT 0,
    instructor_commission NUMERIC(5, 2) NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS lessons (
    id              BIGSERIAL PRIMARY KEY,
    course_id       BIGINT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title           VARCHAR(200) NOT NULL,
    content         TEXT DEFAULT '',
    video_url       VARCHAR(200),
    video           VARCHAR(100),
    notes           VARCHAR(100),
    resources       VARCHAR(100),
    "order"         INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS enrollments (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id       BIGINT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    enrolled_on     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_user_course UNIQUE (user_id, course_id)
);

CREATE TABLE IF NOT EXISTS progress (
    id                  BIGSERIAL PRIMARY KEY,
    enrollment_id       BIGINT NOT NULL UNIQUE REFERENCES enrollments(id) ON DELETE CASCADE,
    completed_lessons   INTEGER NOT NULL DEFAULT 0,
    progress_percent    NUMERIC(5, 2) NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS plans (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(100) UNIQUE NOT NULL,
    description     TEXT NOT NULL DEFAULT '',
    price           NUMERIC(10, 2) NOT NULL,
    duration_days   INTEGER NOT NULL DEFAULT 30,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id         BIGINT NOT NULL REFERENCES plans(id) ON DELETE RESTRICT,
    start_date      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_date        TIMESTAMPTZ,
    status          VARCHAR(20) NOT NULL DEFAULT 'active',
    auto_renew      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS payments (
    id              BIGSERIAL PRIMARY KEY,
    subscription_id BIGINT NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    amount          NUMERIC(10, 2) NOT NULL,
    payment_method  VARCHAR(30),
    payment_status  VARCHAR(20) NOT NULL DEFAULT 'pending',
    transaction_id  VARCHAR(120) UNIQUE,
    invoice_number  VARCHAR(50) UNIQUE,
    paid_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notifications (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title               VARCHAR(160) NOT NULL DEFAULT 'Platform Notification',
    message             TEXT NOT NULL,
    notification_type   VARCHAR(40) NOT NULL DEFAULT 'system',
    icon                VARCHAR(40) NOT NULL DEFAULT 'bi-bell',
    link                VARCHAR(255) NOT NULL DEFAULT '',
    is_read             BOOLEAN NOT NULL DEFAULT FALSE,
    email_sent          BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS activity_logs (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action_type     VARCHAR(80) NOT NULL,
    action_detail   TEXT NOT NULL DEFAULT '',
    ip_address      INET,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS analytics_records (
    id                      BIGSERIAL PRIMARY KEY,
    date                    DATE UNIQUE NOT NULL,
    total_users             INTEGER NOT NULL DEFAULT 0,
    active_subscriptions    INTEGER NOT NULL DEFAULT 0,
    revenue                 NUMERIC(12, 2) NOT NULL DEFAULT 0,
    popular_course_id       BIGINT REFERENCES courses(id) ON DELETE SET NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS attendance (
    id          BIGSERIAL PRIMARY KEY,
    student_id  BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id   BIGINT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    date        DATE NOT NULL,
    status      VARCHAR(10) NOT NULL CHECK (status IN ('Present', 'Absent')),
    marked_by   BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_attendance_student_course_date UNIQUE (student_id, course_id, date)
);

CREATE TABLE IF NOT EXISTS chat_rooms (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(150),
    room_type   VARCHAR(20) NOT NULL DEFAULT 'private',
    created_by  BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_participants (
    id          BIGSERIAL PRIMARY KEY,
    room_id     BIGINT NOT NULL REFERENCES chat_rooms(id) ON DELETE CASCADE,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_room_user UNIQUE (room_id, user_id)
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id           BIGSERIAL PRIMARY KEY,
    room_id      BIGINT NOT NULL REFERENCES chat_rooms(id) ON DELETE CASCADE,
    sender_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message      TEXT,
    message_type VARCHAR(20) NOT NULL DEFAULT 'text',
    file_name    VARCHAR(255),
    file_url     TEXT,
    is_deleted   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS assignments (
    id          BIGSERIAL PRIMARY KEY,
    course_id   BIGINT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title       VARCHAR(200) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    deadline    TIMESTAMPTZ NOT NULL,
    file_url    VARCHAR(500) NOT NULL DEFAULT '',
    created_by  BIGINT NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS submissions (
    id                BIGSERIAL PRIMARY KEY,
    assignment_id     BIGINT NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    student_id        BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    file_url          VARCHAR(500) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    submitted_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    grade             NUMERIC(5, 2) CHECK (grade BETWEEN 0 AND 100),
    remarks           TEXT NOT NULL DEFAULT '',
    graded_at         TIMESTAMPTZ,
    graded_by         BIGINT REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT uq_submission_assignment_student UNIQUE (assignment_id, student_id)
);

-- Helpful indexes for common lookups
CREATE INDEX IF NOT EXISTS idx_courses_instructor ON courses(instructor_id);
CREATE INDEX IF NOT EXISTS idx_lessons_course ON lessons(course_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_user ON enrollments(user_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_plan ON subscriptions(plan_id);
CREATE INDEX IF NOT EXISTS idx_payments_subscription ON payments(subscription_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user_created ON activity_logs(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_attendance_course_date ON attendance(course_id, date);
CREATE INDEX IF NOT EXISTS idx_attendance_student_course ON attendance(student_id, course_id);
CREATE INDEX IF NOT EXISTS idx_assignments_course_deadline ON assignments(course_id, deadline);
CREATE INDEX IF NOT EXISTS idx_submissions_assignment_student ON submissions(assignment_id, student_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_room_created ON chat_messages(room_id, created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_sender ON chat_messages(sender_id);
