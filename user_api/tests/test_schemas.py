import unittest
from datetime import date, timedelta

from pydantic import ValidationError

from app.schemas import (
    AttendanceMarkRequest,
    AttendanceRecordIn,
    LessonCreate,
    LoginRequest,
    PasswordChangeRequest,
    RegisterRequest,
)


class AuthenticationSchemaTests(unittest.TestCase):
    def test_register_normalizes_gmail_and_never_accepts_role(self):
        payload = RegisterRequest(
            name="Khaja Ahmed",
            email="KHAJA1@GMAIL.COM",
            password="DemoPass123!",
        )
        self.assertEqual(str(payload.email), "khaja1@gmail.com")
        with self.assertRaises(ValidationError):
            RegisterRequest(
                name="Unauthorized Instructor",
                email="teacher@gmail.com",
                password="DemoPass123!",
                role="instructor",
            )

    def test_non_gmail_login_is_rejected(self):
        with self.assertRaises(ValidationError):
            LoginRequest(email="student@example.com", password="DemoPass123!")

    def test_weak_password_is_rejected(self):
        with self.assertRaises(ValidationError):
            RegisterRequest(name="Student", email="student@gmail.com", password="password")
        with self.assertRaises(ValidationError):
            PasswordChangeRequest(current_password="OldPass123!", new_password="weakpass")

    def test_video_urls_accept_youtube_and_reject_unsafe_hosts(self):
        lesson = LessonCreate(title="Python", video_url="https://youtu.be/rfscVS0vtbw")
        self.assertEqual(lesson.video_url, "https://youtu.be/rfscVS0vtbw")
        with self.assertRaises(ValidationError):
            LessonCreate(title="Unsafe", video_url="javascript:alert(1)")

    def test_future_attendance_is_rejected(self):
        with self.assertRaises(ValidationError):
            AttendanceMarkRequest(
                course_id=1,
                date=date.today() + timedelta(days=1),
                records=[AttendanceRecordIn(student_id=1, status="Present")],
            )


if __name__ == "__main__":
    unittest.main()
