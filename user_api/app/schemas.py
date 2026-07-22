"""
app/schemas.py

Pydantic schemas for requests and responses.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Role = Literal["student", "instructor"]
CourseStatus = Literal["draft", "published", "archived"]


# ==========================================================
# Authentication
# ==========================================================

class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def require_gmail(cls, value: EmailStr) -> str:
        email = str(value).strip().lower()
        if not email.endswith("@gmail.com"):
            raise ValueError("Please use a valid Gmail address ending with @gmail.com")
        return email

    @field_validator("password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        if not (
            any(char.isupper() for char in value)
            and any(char.islower() for char in value)
            and any(char.isdigit() for char in value)
            and any(not char.isalnum() for char in value)
        ):
            raise ValueError("Password must contain uppercase, lowercase, number, and special character")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def require_gmail(cls, value: EmailStr) -> str:
        email = str(value).strip().lower()
        if not email.endswith("@gmail.com"):
            raise ValueError("Please use a valid Gmail address ending with @gmail.com")
        return email


class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str
    profile_picture: str = ""


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str
    profile_picture: str = ""
    is_active: bool
    date_joined: datetime


class ProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: EmailStr

    @field_validator("email")
    @classmethod
    def require_gmail(cls, value: EmailStr) -> str:
        email = str(value).strip().lower()
        if not email.endswith("@gmail.com"):
            raise ValueError("Please use a valid Gmail address ending with @gmail.com")
        return email


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def strong_password(cls, value: str) -> str:
        if not (
            any(char.isupper() for char in value)
            and any(char.islower() for char in value)
            and any(char.isdigit() for char in value)
            and any(not char.isalnum() for char in value)
        ):
            raise ValueError("Password must contain uppercase, lowercase, number, and special character")
        return value


class ProfilePictureRequest(BaseModel):
    profile_picture: str = Field(default="", max_length=750000)


# ==========================================================
# Lessons
# ==========================================================

class LessonCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = ""
    video_url: str | None = None
    order: int = 0

    @field_validator("video_url")
    @classmethod
    def validate_video_url(cls, value: str | None) -> str | None:
        if not value:
            return None
        value = value.strip()
        parsed = urlparse(value)
        host = (parsed.hostname or "").lower()
        allowed_hosts = {
            "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be",
            "vimeo.com", "www.vimeo.com", "player.vimeo.com",
        }
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Video URL must start with http:// or https://")
        if host not in allowed_hosts and not parsed.path.lower().endswith((".mp4", ".webm", ".ogg")):
            raise ValueError("Use a YouTube, Vimeo, or direct MP4/WebM/Ogg video URL")
        return value


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    video_url: str | None
    order: int


# ==========================================================
# Courses
# ==========================================================

class CourseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""

    thumbnail: str | None = None
    duration: str = "0 Hours"
    level: str = "Beginner"

    status: CourseStatus = "draft"

    is_premium: bool = False

    price: Decimal = Decimal("0.00")

    instructor_commission: Decimal = Decimal("0.00")


class CourseUpdate(BaseModel):
    title: str | None = None
    description: str | None = None

    thumbnail: str | None = None
    duration: str | None = None
    level: str | None = None

    status: CourseStatus | None = None

    is_premium: bool | None = None

    price: Decimal | None = None

    instructor_commission: Decimal | None = None


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    title: str
    description: str

    thumbnail: str | None
    duration: str
    level: str

    instructor_id: int

    status: str

    is_premium: bool

    price: Decimal

    instructor_commission: Decimal

    created_at: datetime

    updated_at: datetime


class CourseDetailOut(CourseOut):
    lessons: list[LessonOut] = []


# ==========================================================
# Enrollment
# ==========================================================

class EnrollRequest(BaseModel):
    course_id: int


class EnrollmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    course_id: int
    enrolled_on: datetime


# ==========================================================
# Progress
# ==========================================================

class ProgressUpdateRequest(BaseModel):
    enrollment_id: int
    completed_lessons: int = Field(ge=0)


class ProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    enrollment_id: int
    completed_lessons: int
    progress_percent: Decimal


# ==========================================================
# Plans
# ==========================================================

class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    price: Decimal
    duration_days: int


# ==========================================================
# Subscription
# ==========================================================

class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    plan_id: int

    start_date: datetime
    end_date: datetime

    status: str
    auto_renew: bool


class SubscribeRequest(BaseModel):
    plan_id: int


# ==========================================================
# Payment
# ==========================================================

class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal

    payment_status: str
    payment_method: str | None

    transaction_id: str | None
    invoice_number: str | None
    paid_at: datetime


# ==========================================================
# Notifications
# ==========================================================

class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    icon: str
    link: str
    is_read: bool
    email_sent: bool
    created_at: datetime


class MarkNotificationReadRequest(BaseModel):
    notification_ids: list[int] | None = None


class BroadcastNotificationRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    message: str = Field(min_length=1)
    link: str = ""


# ==========================================================
# Activity
# ==========================================================

class ActivityLogCreate(BaseModel):
    action_type: str = Field(min_length=1, max_length=80)
    action_detail: str = ""


class ActivityLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    action_type: str
    action_detail: str
    ip_address: str | None
    created_at: datetime


# ==========================================================
# Analytics
# ==========================================================

class AnalyticsOverviewOut(BaseModel):
    total_users: int
    new_users_today: int
    new_users_this_month: int
    active_users: int
    inactive_users: int
    student_count: int
    instructor_count: int
    total_courses: int
    published_courses: int
    premium_courses: int
    free_courses: int
    active_subscriptions: int
    expired_subscriptions: int
    renewed_subscriptions: int
    cancelled_subscriptions: int
    new_subscriptions: int
    todays_revenue: Decimal
    monthly_revenue: Decimal
    total_revenue: Decimal
    popular_course: str | None
    completion_rate: Decimal
    successful_payments: int
    failed_payments: int
    activity_count: int
    daily_activity: int
    weekly_activity: int
    unread_notifications: int


class MonthlyRevenueOut(BaseModel):
    month: date
    revenue: Decimal


class RevenueByPlanOut(BaseModel):
    plan: str
    revenue: Decimal

# ==========================================================
# Chat
# ==========================================================

class ChatRoomCreate(BaseModel):
    name: str | None = None
    room_type: Literal["private", "group"] = "private"
    participant_ids: list[int] = Field(min_length=1)


class ChatRoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None
    room_type: str
    created_by: int
    created_at: datetime


class ChatParticipantInfo(BaseModel):
    id: int
    name: str
    role: str
    profile_picture: str = ""
    online: bool = False
    last_seen: str | None = None


class ChatRoomSummary(BaseModel):
    id: int
    name: str | None
    display_name: str
    room_type: str
    created_by: int
    created_at: datetime
    participants: list[ChatParticipantInfo]
    unread_count: int = 0
    last_message: str = ""
    last_message_at: datetime | None = None


class ChatParticipantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    user_id: int
    joined_at: datetime


class ChatMessageCreate(BaseModel):
    room_id: int
    message: str | None = None
    message_type: Literal[
        "text",
        "image",
        "pdf",
        "doc",
        "system",
    ] = "text"


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_id: int
    sender_id: int
    sender_name: str = ""

    message: str | None

    message_type: str

    file_name: str | None

    file_url: str | None

    is_deleted: bool

    created_at: datetime
    delivery_status: Literal["sent", "delivered", "read"] = "sent"
    delivered_at: datetime | None = None
    read_at: datetime | None = None


class FileMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int

    room_id: int

    sender_id: int

    file_name: str

    file_url: str

    created_at: datetime

class ChatMessagePage(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
    messages: list[ChatMessageOut]


class ChatReadResponse(BaseModel):
    room_id: int
    read_count: int


# ==========================================================
# Attendance and assignments
# ==========================================================

class AttendanceRecordIn(BaseModel):
    student_id: int = Field(gt=0)
    status: Literal["Present", "Absent", "Late"]


class AttendanceMarkRequest(BaseModel):
    course_id: int = Field(gt=0)
    date: date
    records: list[AttendanceRecordIn] = Field(min_length=1)

    @field_validator("date")
    @classmethod
    def prevent_future_attendance(cls, value: date) -> date:
        if value > datetime.now(timezone.utc).date():
            raise ValueError("Attendance cannot be marked for a future date")
        return value


class AttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    course_id: int
    date: date
    status: str
    marked_by: int
    created_at: datetime


class AttendanceSummary(BaseModel):
    total: int
    present: int
    absent: int
    late: int = 0
    percentage: Decimal
    records: list[AttendanceOut]


class AssignmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    course_id: int
    title: str
    description: str
    deadline: datetime
    file_url: str
    created_by: int
    created_at: datetime


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    assignment_id: int
    student_id: int
    student_name: str = "Student"
    student_email: str = ""
    assignment_title: str = "Assignment"
    file_url: str
    original_filename: str
    submitted_at: datetime
    grade: Decimal | None
    remarks: str
    graded_at: datetime | None
    graded_by: int | None


class GradeSubmissionRequest(BaseModel):
    submission_id: int = Field(gt=0)
    grade: Decimal = Field(ge=0, le=100)
    remarks: str = Field(default="", max_length=2000)
