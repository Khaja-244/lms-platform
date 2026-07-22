from datetime import timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone

from accounts.models import User, UserRole
from courses.models import Course, Enrollment, Progress
from payments.models import Payment
from subscriptions.models import Subscription, SubscriptionStatus

from .models import ActivityLog, AnalyticsRecord, ChatMessage, Notification


class ActivityLogService:
    @staticmethod
    def client_ip(request):
        if request is None:
            return None
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    @staticmethod
    def log(user, action_type, description="", request=None):
        if not user or not getattr(user, "is_authenticated", False):
            return None
        return ActivityLog.objects.create(
            user=user,
            action_type=action_type,
            action_detail=description,
            ip_address=ActivityLogService.client_ip(request),
        )


class NotificationService:
    DEFAULT_ICONS = {
        "welcome_registration": "bi-person-check",
        "payment_success": "bi-credit-card-2-front",
        "payment_failed": "bi-exclamation-octagon",
        "subscription_activated": "bi-patch-check",
        "subscription_renewed": "bi-arrow-repeat",
        "subscription_expiring": "bi-hourglass-split",
        "subscription_expired": "bi-calendar-x",
        "course_purchased": "bi-bag-check",
        "course_enrolled": "bi-journal-check",
        "course_update": "bi-megaphone",
        "new_lesson_published": "bi-play-circle",
        "password_changed": "bi-shield-lock",
        "instructor_message": "bi-chat-dots",
        "admin_broadcast": "bi-broadcast",
        "system": "bi-bell",
    }

    @classmethod
    def create(cls, user, title, message, notification_type="system", link="", email_sent=False):
        return Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            icon=cls.DEFAULT_ICONS.get(notification_type, "bi-bell"),
            link=link,
            email_sent=email_sent,
        )

    @classmethod
    def broadcast(cls, title, message, link="", email_sent=False):
        users = User.objects.filter(is_active=True).exclude(role=UserRole.ADMIN)
        return [
            cls.create(user, title, message, "admin_broadcast", link, email_sent)
            for user in users
        ]


class AnalyticsService:
    @staticmethod
    def dashboard_context():
        today = timezone.localdate()
        now = timezone.now()
        month_start = today.replace(day=1)
        week_start = today - timedelta(days=6)

        users = User.objects.exclude(role=UserRole.ADMIN)
        courses = Course.objects.all()
        subscriptions = Subscription.objects.all()
        payments = Payment.objects.all()
        success_payments = payments.filter(payment_status="success")
        failed_payments = payments.filter(payment_status="failed")

        top_courses = (
            courses.annotate(enrollment_count=Count("enrollments"))
            .order_by("-enrollment_count", "title")[:8]
        )
        most_popular_course = top_courses[0] if top_courses else None

        total_lessons_completed = Progress.objects.aggregate(total=Sum("completed_lessons")).get("total") or 0
        total_lessons_possible = sum(
            enrollment.course.lessons.count()
            for enrollment in Enrollment.objects.select_related("course").prefetch_related("course__lessons")
        )
        completion_rate = 0
        if total_lessons_possible:
            completion_rate = round((total_lessons_completed / total_lessons_possible) * 100, 2)

        activity_daily = (
            ActivityLog.objects.filter(created_at__date__gte=today - timedelta(days=13))
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        revenue_monthly = (
            success_payments.annotate(month=TruncMonth("paid_at"))
            .values("month")
            .annotate(total=Sum("amount"))
            .order_by("month")[:12]
        )
        revenue_by_plan = (
            success_payments.values("subscription__plan__name")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        enrollment_trends = (
            Enrollment.objects.filter(enrolled_on__date__gte=today - timedelta(days=13))
            .annotate(day=TruncDate("enrolled_on"))
            .values("day")
            .annotate(count=Count("id"))
            .order_by("day")
        )
        chat_daily = (
            ChatMessage.objects.filter(is_deleted=False, created_at__date__gte=today - timedelta(days=13))
            .annotate(day=TruncDate("created_at")).values("day").annotate(count=Count("id")).order_by("day")
        )
        active_chat_users = (
            ChatMessage.objects.filter(is_deleted=False).values("sender__name")
            .annotate(message_count=Count("id")).order_by("-message_count")[:5]
        )

        monthly_revenue = success_payments.filter(paid_at__date__gte=month_start).aggregate(total=Sum("amount")).get("total") or 0
        total_users = users.count()
        active_subscriptions = subscriptions.filter(status=SubscriptionStatus.ACTIVE, end_date__gte=now).count()

        AnalyticsRecord.objects.update_or_create(
            date=today,
            defaults={
                "total_users": total_users,
                "active_subscriptions": active_subscriptions,
                "revenue": monthly_revenue,
                "popular_course": most_popular_course,
            },
        )

        return {
            "total_users": total_users,
            "new_users_today": users.filter(date_joined__date=today).count(),
            "new_users_this_month": users.filter(date_joined__date__gte=month_start).count(),
            "active_users": users.filter(is_active=True).count(),
            "inactive_users": users.filter(is_active=False).count(),
            "student_count": users.filter(role=UserRole.STUDENT).count(),
            "instructor_count": users.filter(role=UserRole.INSTRUCTOR).count(),
            "total_courses": courses.count(),
            "published_courses": courses.filter(status="published").count(),
            "premium_courses": courses.filter(is_premium=True).count(),
            "free_courses": courses.filter(is_premium=False).count(),
            "most_popular_course": most_popular_course.title if most_popular_course else "No enrollments yet",
            "completion_rate": completion_rate,
            "active_subscriptions": active_subscriptions,
            "expired_subscriptions": subscriptions.filter(status=SubscriptionStatus.EXPIRED).count(),
            "renewed_subscriptions": subscriptions.filter(auto_renew=True).count(),
            "cancelled_subscriptions": subscriptions.filter(status=SubscriptionStatus.CANCELLED).count(),
            "new_subscriptions": subscriptions.filter(created_at__date__gte=month_start).count(),
            "todays_revenue": success_payments.filter(paid_at__date=today).aggregate(total=Sum("amount")).get("total") or 0,
            "monthly_revenue": monthly_revenue,
            "total_revenue": success_payments.aggregate(total=Sum("amount")).get("total") or 0,
            "successful_payments": success_payments.count(),
            "failed_payments": failed_payments.count(),
            "daily_activity": ActivityLog.objects.filter(created_at__date=today).count(),
            "weekly_activity": ActivityLog.objects.filter(created_at__date__gte=week_start).count(),
            "recent_logs": ActivityLog.objects.select_related("user")[:10],
            "recent_payments": Payment.objects.select_related("subscription", "subscription__user", "subscription__plan")[:8],
            "recent_notifications": Notification.objects.select_related("user")[:8],
            "unread_notifications": Notification.objects.filter(is_read=False).count(),
            "popular_course_labels": [course.title for course in top_courses],
            "popular_course_values": [course.enrollment_count for course in top_courses],
            "activity_labels": [str(row["day"]) for row in activity_daily],
            "activity_values": [row["count"] for row in activity_daily],
            "revenue_labels": [row["month"].strftime("%b %Y") for row in revenue_monthly if row["month"]],
            "revenue_values": [float(row["total"] or 0) for row in revenue_monthly],
            "revenue_by_plan_labels": [row["subscription__plan__name"] or "Unknown" for row in revenue_by_plan],
            "revenue_by_plan_values": [float(row["total"] or 0) for row in revenue_by_plan],
            "enrollment_labels": [str(row["day"]) for row in enrollment_trends],
            "enrollment_values": [row["count"] for row in enrollment_trends],
            "course_mix_values": [courses.filter(is_premium=True).count(), courses.filter(is_premium=False).count()],
            "total_chat_messages": ChatMessage.objects.filter(is_deleted=False).count(),
            "chat_messages_today": ChatMessage.objects.filter(is_deleted=False, created_at__date=today).count(),
            "chat_labels": [str(row["day"]) for row in chat_daily],
            "chat_values": [row["count"] for row in chat_daily],
            "active_chat_users": active_chat_users,
        }
