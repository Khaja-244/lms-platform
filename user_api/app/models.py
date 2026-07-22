"""
app/models.py

SQLAlchemy models for the shared PostgreSQL database.

Django is responsible for creating migrations.
FastAPI only reads/writes the existing tables.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Boolean,
    Date,
    UniqueConstraint,
    func,
    Enum,
)
from sqlalchemy.orm import relationship

from .database import Base


# ==========================================================
# User
# ==========================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=False)
    email = Column(String(254), unique=True, nullable=False, index=True)
    role = Column(String(20), nullable=False, default="student")
    profile_picture = Column(Text, nullable=False, default="")

    # Matches Django's db_column="password_hash"
    password_hash = Column("password_hash", String(128), nullable=False)

    is_active = Column(Boolean, nullable=False, default=True)
    is_staff = Column(Boolean, nullable=False, default=False)
    is_superuser = Column(Boolean, nullable=False, default=False)

    date_joined = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    courses_taught = relationship(
        "Course",
        back_populates="instructor",
    )

    enrollments = relationship(
        "Enrollment",
        back_populates="user",
    )


# ==========================================================
# Course
# ==========================================================
class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(200), nullable=False)

    description = Column(Text, default="")

    thumbnail = Column(
        String(255),
        nullable=True,
    )

    duration = Column(
        String(100),
        nullable=False,
        default="0 Hours",
    )

    level = Column(
        String(30),
        nullable=False,
        default="Beginner",
    )

    instructor_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    status = Column(
        String(20),
        default="draft",
    )

    is_premium = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    price = Column(
        Numeric(10, 2),
        default=0,
        nullable=False,
    )

    instructor_commission = Column(
        Numeric(5, 2),
        default=0,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ==========================
    # Relationships
    # ==========================

    instructor = relationship(
        "User",
        back_populates="courses_taught",
    )

    lessons = relationship(
        "Lesson",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    enrollments = relationship(
        "Enrollment",
        back_populates="course",
        cascade="all, delete-orphan",
    )

# ==========================================================
# Lesson
# ==========================================================
class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)

    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=False,
    )

    title = Column(String(200), nullable=False)
    content = Column(Text, default="")
    video_url = Column(String(200), nullable=True)
    order = Column(Integer, default=0)

    course = relationship(
        "Course",
        back_populates="lessons",
    )


# ==========================================================
# Enrollment
# ==========================================================
class Enrollment(Base):
    __tablename__ = "enrollments"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "course_id",
            name="uq_user_course",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=False,
    )

    enrolled_on = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user = relationship(
        "User",
        back_populates="enrollments",
    )

    course = relationship(
        "Course",
        back_populates="enrollments",
    )

    progress = relationship(
        "Progress",
        back_populates="enrollment",
        uselist=False,
        cascade="all, delete-orphan",
    )


# ==========================================================
# Progress
# ==========================================================
class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)

    enrollment_id = Column(
        Integer,
        ForeignKey("enrollments.id"),
        unique=True,
        nullable=False,
    )

    completed_lessons = Column(
        Integer,
        default=0,
    )

    progress_percent = Column(
        Numeric(5, 2),
        default=0,
    )

    enrollment = relationship(
        "Enrollment",
        back_populates="progress",
    )


# ==========================================================
# Plan
# ==========================================================

class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    description = Column(Text)

    price = Column(Numeric(10, 2), nullable=False)

    duration_days = Column(Integer, nullable=False)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    subscriptions = relationship(
        "Subscription",
        back_populates="plan",
    )


# ==========================================================
# Subscription
# ==========================================================

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    plan_id = Column(Integer, ForeignKey("plans.id"))

    start_date = Column(DateTime(timezone=True))

    end_date = Column(DateTime(timezone=True))

    status = Column(String(20), default="active")

    auto_renew = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User")

    plan = relationship(
        "Plan",
        back_populates="subscriptions",
    )

    payments = relationship(
        "Payment",
        back_populates="subscription",
    )


# ==========================================================
# Payment
# ==========================================================

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))

    amount = Column(Numeric(10, 2))

    payment_method = Column(String(30))

    payment_status = Column(String(20))

    transaction_id = Column(String(120))

    invoice_number = Column(String(50))

    paid_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True))

    updated_at = Column(DateTime(timezone=True))

    subscription = relationship(
        "Subscription",
        back_populates="payments",
    )


# ==========================================================
# Notification
# ==========================================================

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(160), nullable=False, default="Platform Notification")
    message = Column(Text, nullable=False)
    notification_type = Column(String(40), nullable=False, default="system")
    icon = Column(String(40), nullable=False, default="bi-bell")
    link = Column(String(255), nullable=False, default="")
    is_read = Column(Boolean, nullable=False, default=False)
    email_sent = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User")


# ==========================================================
# Activity Log
# ==========================================================

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action_type = Column(String(80), nullable=False)
    action_detail = Column(Text, default="")
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User")


# ==========================================================
# Analytics Record
# ==========================================================

class AnalyticsRecord(Base):
    __tablename__ = "analytics_records"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False)
    total_users = Column(Integer, default=0, nullable=False)
    active_subscriptions = Column(Integer, default=0, nullable=False)
    revenue = Column(Numeric(12, 2), default=0, nullable=False)
    popular_course_id = Column(Integer, ForeignKey("courses.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    popular_course = relationship("Course")



# ==========================================================
# Chat Room
# ==========================================================

class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=True)

    room_type = Column(
        String(20),
        nullable=False,
        default="private",
    )

    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    creator = relationship("User")

    participants = relationship(
        "ChatParticipant",
        back_populates="room",
        cascade="all, delete-orphan",
    )

    messages = relationship(
        "ChatMessage",
        back_populates="room",
        cascade="all, delete-orphan",
    )


# ==========================================================
# Chat Participant
# ==========================================================

class ChatParticipant(Base):
    __tablename__ = "chat_participants"

    __table_args__ = (
        UniqueConstraint(
            "room_id",
            "user_id",
            name="uq_room_user",
        ),
    )

    id = Column(Integer, primary_key=True)

    room_id = Column(
        Integer,
        ForeignKey("chat_rooms.id"),
        nullable=False,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    joined_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    room = relationship(
        "ChatRoom",
        back_populates="participants",
    )

    user = relationship("User")


# ==========================================================
# Chat Message
# ==========================================================

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)

    room_id = Column(
        Integer,
        ForeignKey("chat_rooms.id"),
        nullable=False,
    )

    sender_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    message = Column(
        Text,
        nullable=True,
    )

    message_type = Column(
        String(20),
        nullable=False,
        default="text",
    )

    file_name = Column(
        String(255),
        nullable=True,
    )

    file_url = Column(
        Text,
        nullable=True,
    )

    is_deleted = Column(
        Boolean,
        default=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    room = relationship(
        "ChatRoom",
        back_populates="messages",
    )

    sender = relationship("User")


class ChatMessageReceipt(Base):
    __tablename__ = "chat_message_receipts"
    __table_args__ = (
        UniqueConstraint(
            "message_id",
            "user_id",
            name="uq_chat_receipt_message_user",
        ),
    )

    id = Column(Integer, primary_key=True)
    message_id = Column(
        Integer,
        ForeignKey("chat_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    message = relationship("ChatMessage")
    user = relationship("User")


# ==========================================================
# Attendance and assignments (Task 5)
# ==========================================================

class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", "date", name="uq_attendance_student_course_date"),
    )

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    status = Column(String(10), nullable=False)
    marked_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    student = relationship("User", foreign_keys=[student_id])
    course = relationship("Course")
    marker = relationship("User", foreign_keys=[marked_by])


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False, default="")
    deadline = Column(DateTime(timezone=True), nullable=False)
    file_url = Column(String(500), nullable=False, default="")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    course = relationship("Course")
    creator = relationship("User")
    submissions = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint("assignment_id", "student_id", name="uq_submission_assignment_student"),
    )

    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    file_url = Column(String(500), nullable=False)
    original_filename = Column(String(255), nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    grade = Column(Numeric(5, 2), nullable=True)
    remarks = Column(Text, nullable=False, default="")
    graded_at = Column(DateTime(timezone=True), nullable=True)
    graded_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("User", foreign_keys=[student_id])
    grader = relationship("User", foreign_keys=[graded_by])

    @property
    def student_name(self):
        return self.student.name if self.student else "Student"

    @property
    def student_email(self):
        return self.student.email if self.student else ""

    @property
    def assignment_title(self):
        return self.assignment.title if self.assignment else "Assignment"
