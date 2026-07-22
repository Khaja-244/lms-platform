"""
courses/models.py

These four tables are shared with FastAPI exactly as listed in the
task's "Database Models" section:
    Course     (id, title, description, instructor_id, status)
    Lesson     (id, course_id, title, content, video_url)
    Enrollment (id, user_id, course_id, enrolled_on)
    Progress   (id, enrollment_id, completed_lessons, progress_percent)

Django owns the migrations (source of truth for the schema).
FastAPI's SQLAlchemy models in user_api/app/models.py mirror these
table/column names so both services read and write the same rows.
"""

from django.conf import settings
from django.db import models
from django.core.validators import FileExtensionValidator

class CourseStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PUBLISHED = "published", "Published"
    ARCHIVED = "archived", "Archived"


class Course(models.Model):
    title = models.CharField(max_length=200)

    description = models.TextField(blank=True)
    thumbnail = models.ImageField(
        upload_to="course_thumbnails/",
        blank=True,
        null=True,
    )

    duration = models.CharField(
        max_length=100,
        default="0 Hours",
    )

    level = models.CharField(
        max_length=30,
        choices=[
            ("Beginner", "Beginner"),
            ("Intermediate", "Intermediate"),
            ("Advanced", "Advanced"),
        ],
        default="Beginner",
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courses_taught",
        db_column="instructor_id",
        limit_choices_to={"role": "instructor"},
    )

    status = models.CharField(
        max_length=20,
        choices=CourseStatus.choices,
        default=CourseStatus.DRAFT,
    )

    is_premium = models.BooleanField(default=False)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    instructor_commission = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Commission percentage",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "courses"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def enrolled_count(self):
        return self.enrollments.count()


class Lesson(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="lessons", db_column="course_id"
    )
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)

    video_url = models.URLField(
        blank=True,
        null=True,
    )

    video = models.FileField(
        upload_to="lesson_videos/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(["mp4", "mov", "avi", "mkv"])
        ],
    )

    notes = models.FileField(
        upload_to="lesson_notes/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(["pdf"])
        ],
    )

    resources = models.FileField(
        upload_to="lesson_resources/",
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(["zip"])
        ],
    )
    order = models.PositiveIntegerField(default=0, help_text="Display order within the course")

    class Meta:
        db_table = "lessons"
        ordering = ["course", "order", "id"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class Enrollment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="enrollments",
        db_column="user_id",
        limit_choices_to={"role": "student"},
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollments", db_column="course_id"
    )
    enrolled_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "enrollments"
        unique_together = ("user", "course")  # a student can't enroll twice in the same course
        ordering = ["-enrolled_on"]

    def __str__(self):
        return f"{self.user.name} -> {self.course.title}"


class Progress(models.Model):
    enrollment = models.OneToOneField(
        Enrollment, on_delete=models.CASCADE, related_name="progress", db_column="enrollment_id"
    )
    completed_lessons = models.PositiveIntegerField(default=0)
    progress_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = "progress"

    def __str__(self):
        return f"{self.enrollment} - {self.progress_percent}%"

    def recalculate(self):
        """Recompute progress_percent from completed_lessons / total lessons in the course."""
        total_lessons = self.enrollment.course.lessons.count()
        if total_lessons == 0:
            self.progress_percent = 0
        else:
            self.progress_percent = round((self.completed_lessons / total_lessons) * 100, 2)
        self.save(update_fields=["progress_percent"])


class Attendance(models.Model):
    STATUS_CHOICES = (("Present", "Present"), ("Absent", "Absent"), ("Late", "Late"))
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendance_records", db_column="student_id")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="attendance_records", db_column="course_id")
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    marked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="attendance_marked", db_column="marked_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "attendance"
        ordering = ["-date", "student_id"]
        constraints = [models.UniqueConstraint(fields=["student", "course", "date"], name="uq_attendance_student_course_date")]
        indexes = [
            models.Index(fields=["course", "date"], name="attendance_course_date_idx"),
            models.Index(fields=["student", "course"], name="attendance_student_course_idx"),
        ]


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments", db_column="course_id")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    deadline = models.DateTimeField()
    file_url = models.CharField(max_length=500, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="assignments_created", db_column="created_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "assignments"
        ordering = ["deadline"]
        indexes = [models.Index(fields=["course", "deadline"], name="assignment_course_deadline_idx")]

    def __str__(self):
        return f"{self.course}: {self.title}"


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions", db_column="assignment_id")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assignment_submissions", db_column="student_id")
    file_url = models.CharField(max_length=500)
    original_filename = models.CharField(max_length=255)
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    graded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="submissions_graded", db_column="graded_by")

    class Meta:
        db_table = "submissions"
        ordering = ["-submitted_at"]
        constraints = [models.UniqueConstraint(fields=["assignment", "student"], name="uq_submission_assignment_student")]
        indexes = [models.Index(fields=["assignment", "student"], name="submission_asgn_student_idx")]
