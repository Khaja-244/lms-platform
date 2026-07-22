import os

from django.shortcuts import render


def _context(**extra):
    data = {
        "fastapi_base_url": os.environ.get("FASTAPI_BASE_URL", "http://localhost:8001"),
    }
    data.update(extra)
    return data


def login_view(request):
    return render(request, "student/login.html", _context())


def register_view(request):
    return render(request, "student/register.html", _context())


def dashboard_view(request):
    return render(request, "student/dashboard.html", _context())


def courses_view(request):
    return render(request, "student/courses.html", _context())


def course_detail_view(request, course_id):
    return render(
        request,
        "student/course_detail.html",
        _context(course_id=course_id),
    )


def my_courses_view(request):
    return render(request, "student/my_courses.html", _context())


def lesson_player_view(request, lesson_id):
    return render(
        request,
        "student/lesson_player.html",
        _context(lesson_id=lesson_id),
    )


def plans_view(request):
    return render(request, "student/plans.html", _context())


def subscription_view(request):
    return render(request, "student/subscription.html", _context())


def payments_view(request):
    return render(request, "student/payments.html", _context())


def notifications_view(request):
    return render(request, "student/notifications.html", _context())


def profile_view(request):
    return render(request, "student/profile.html", _context())


def assignments_view(request):
    return render(request, "student/assignments.html", _context())


def attendance_view(request):
    return render(request, "student/attendance.html", _context())


def chat_view(request):
    return render(request, "student/chat.html", _context())
