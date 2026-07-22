from django.contrib import admin

from .models import Assignment, Attendance, Course, Enrollment, Lesson, Progress, Submission


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "title",
        "instructor",
        "status",
        "duration",
        "level",
        "is_premium",
        "price",
        "instructor_commission",
        "enrolled_count",
        "created_at",
    )

    list_filter = (
        "status",
        "is_premium",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "instructor__name",
        "instructor__email",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "enrolled_count",
    )

    list_per_page = 10

    fieldsets = (
        (
            "Course Information",
            {
                "fields": (
                    "title",
                    "description",
                    "thumbnail",
                    "duration",
                    "level",
                    "instructor",
                    "status",
                )
            },
        ),
        (
            "Subscription Settings",
            {
                "fields": (
                    "is_premium",
                    "price",
                    "instructor_commission",
                )
            },
        ),
        (
            "Audit",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    inlines = [LessonInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "course",
        "enrolled_on",
    )

    list_filter = (
        "course",
        "enrolled_on",
    )

    search_fields = (
        "user__name",
        "user__email",
        "course__title",
    )

    ordering = (
        "-enrolled_on",
    )

    list_per_page = 10


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "enrollment",
        "completed_lessons",
        "progress_percent",
    )

    search_fields = (
        "enrollment__user__email",
        "enrollment__course__title",
    )

    ordering = (
        "-id",
    )

    list_per_page = 10


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "date", "status", "marked_by")
    list_filter = ("course", "date", "status")
    search_fields = ("student__email", "course__title")


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "deadline", "created_by", "created_at")
    list_filter = ("course", "deadline")
    search_fields = ("title", "course__title")


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("assignment", "student", "submitted_at", "grade", "graded_by")
    list_filter = ("assignment__course", "submitted_at")
    search_fields = ("student__email", "assignment__title")
