"""
dashboard/views.py

Task spec: "Dashboard showing total users, courses, and enrollments"
           "Reports using Chart.js (e.g., top enrolled courses)"
"""

import json

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render

from accounts.models import User, UserRole
from courses.models import Course, Enrollment, Lesson


@login_required
def index(request):
    """Main dashboard page: summary cards + a Chart.js bar chart."""

    total_students = User.objects.filter(role=UserRole.STUDENT).count()
    total_instructors = User.objects.filter(role=UserRole.INSTRUCTOR).count()
    total_courses = Course.objects.count()
    total_lessons = Lesson.objects.count()
    total_enrollments = Enrollment.objects.count()

    # Top 5 enrolled courses, used to feed the Chart.js bar chart below.
    top_courses = (
        Course.objects.annotate(enrollment_count=Count("enrollments"))
        .order_by("-enrollment_count")[:5]
    )
    chart_labels = [c.title for c in top_courses]
    chart_data = [c.enrollment_count for c in top_courses]

    recent_users = User.objects.exclude(role=UserRole.ADMIN).order_by("-date_joined")[:4]
    recent_courses = Course.objects.select_related("instructor").order_by("-created_at")[:4]
    recent_enrollments = (
        Enrollment.objects.select_related("user", "course")
        .order_by("-enrolled_on")[:4]
    )

    context = {
        "total_students": total_students,
        "total_instructors": total_instructors,
        "total_courses": total_courses,
        "total_lessons": total_lessons,
        "total_enrollments": total_enrollments,
        "chart_labels": json.dumps(chart_labels),
        "chart_data": json.dumps(chart_data),
        "recent_users": recent_users,
        "recent_courses": recent_courses,
        "recent_enrollments": recent_enrollments,
    }
    return render(request, "dashboard/index.html", context)


@login_required
def top_courses_api(request):
    """
    Optional JSON endpoint (used if you want to refresh the chart via
    fetch() instead of rendering it server-side). Not required by the
    task but handy for a live-updating dashboard.
    """
    top_courses = (
        Course.objects.annotate(enrollment_count=Count("enrollments"))
        .order_by("-enrollment_count")[:5]
    )
    return JsonResponse({
        "labels": [c.title for c in top_courses],
        "data": [c.enrollment_count for c in top_courses],
    })
