from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.db.models import Avg, Count, Q

from courses.models import Assignment, Attendance, Course, Enrollment

from .forms import NotificationForm
from .models import Notification
from .services import AnalyticsService, NotificationService


@login_required
def analytics_dashboard(request):
    return render(request, "analytics/dashboard.html", AnalyticsService.dashboard_context())


@login_required
def course_dashboard_json(request):
    course_id = request.GET.get("course_id")
    if not course_id or not course_id.isdigit():
        return JsonResponse({"error": "A valid course_id is required"}, status=400)
    course = get_object_or_404(Course.objects.select_related("instructor"), pk=int(course_id))
    if request.user.role == "instructor" and course.instructor_id != request.user.id:
        return JsonResponse({"error": "You can only view analytics for your own courses"}, status=403)
    attendance = Attendance.objects.filter(course=course).aggregate(
        total=Count("id"), present=Count("id", filter=Q(status="Present")))
    total, present = attendance["total"] or 0, attendance["present"] or 0
    assignment_stats = Assignment.objects.filter(course=course).aggregate(
        total_assignments=Count("id"), submissions_count=Count("submissions"), average_grade=Avg("submissions__grade"))
    average_grade = assignment_stats["average_grade"]
    return JsonResponse({
        "course_id": course.id,
        "course_title": course.title,
        "total_students": Enrollment.objects.filter(course=course).values("user_id").distinct().count(),
        "avg_attendance": round(present * 100 / total, 2) if total else 0,
        "total_assignments": assignment_stats["total_assignments"],
        "submissions_count": assignment_stats["submissions_count"],
        "average_grade": round(float(average_grade), 2) if average_grade is not None else None,
    })


@login_required
def notification_list(request):
    notifications = Notification.objects.select_related("user").all()
    return render(request, "analytics/notification_list.html", {"notifications": notifications})


@login_required
def notification_create(request):
    if request.method == "POST":
        form = NotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            NotificationService.create(
                user=notification.user,
                title=notification.title,
                message=notification.message,
                notification_type=notification.notification_type,
                link=notification.link,
                email_sent=notification.email_sent,
            )
            messages.success(request, "Notification created successfully.")
            return redirect("analytics:notification_list")
    else:
        form = NotificationForm()
    return render(request, "analytics/notification_form.html", {"form": form})


@login_required
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    messages.success(request, "Notification marked as read.")
    return redirect("analytics:notification_list")


@login_required
def notification_mark_all_read(request):
    query = Notification.objects.filter(is_read=False)
    if getattr(request.user, "role", "") != "admin":
        query = query.filter(user=request.user)
    query.update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect("analytics:notification_list")
