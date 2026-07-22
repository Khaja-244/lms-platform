from django.conf import settings
from django.db import models
from django.utils import timezone

from courses.models import Course


class NotificationType(models.TextChoices):
    WELCOME_REGISTRATION = "welcome_registration", "Welcome Registration"
    PAYMENT_SUCCESS = "payment_success", "Payment Success"
    PAYMENT_FAILED = "payment_failed", "Payment Failed"
    SUBSCRIPTION_ACTIVATED = "subscription_activated", "Subscription Activated"
    SUBSCRIPTION_RENEWED = "subscription_renewed", "Subscription Renewed"
    SUBSCRIPTION_EXPIRING = "subscription_expiring", "Subscription Expiring"
    SUBSCRIPTION_EXPIRED = "subscription_expired", "Subscription Expired"
    COURSE_PURCHASED = "course_purchased", "Course Purchased"
    COURSE_ENROLLED = "course_enrolled", "Course Enrolled"
    PLAN_EXPIRY = "plan_expiry", "Plan Expiry"
    COURSE_UPDATE = "course_update", "Course Update"
    NEW_LESSON_PUBLISHED = "new_lesson_published", "New Lesson Published"
    PASSWORD_CHANGED = "password_changed", "Password Changed"
    INSTRUCTOR_MESSAGE = "instructor_message", "Instructor Message"
    ADMIN_BROADCAST = "admin_broadcast", "Admin Broadcast"
    SYSTEM = "system", "System"


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        db_column="user_id",
    )
    title = models.CharField(max_length=160, default="Platform Notification")
    message = models.TextField()
    notification_type = models.CharField(
        max_length=40,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
    )
    icon = models.CharField(max_length=40, default="bi-bell")
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.title}"


class ActivityLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="activity_logs",
        db_column="user_id",
    )
    action_type = models.CharField(max_length=80)
    action_detail = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "activity_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["action_type"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.action_type}"


class AnalyticsRecord(models.Model):
    date = models.DateField(unique=True)
    total_users = models.PositiveIntegerField(default=0)
    active_subscriptions = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    popular_course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analytics_records",
        db_column="popular_course_id",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "analytics_records"
        ordering = ["-date"]

    def __str__(self):
        return f"Analytics - {self.date}"


class ChatMessage(models.Model):
    room_id = models.BigIntegerField()
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, db_column="sender_id", related_name="chat_messages")
    message = models.TextField(blank=True, null=True)
    message_type = models.CharField(max_length=20, default="text")
    file_name = models.CharField(max_length=255, blank=True, null=True)
    file_url = models.TextField(blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = "chat_messages"
        ordering = ["-created_at"]


class ChatMessageReceipt(models.Model):
    message_id = models.BigIntegerField(db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column="user_id",
        related_name="chat_receipts",
    )
    delivered_at = models.DateTimeField(blank=True, null=True)
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "chat_message_receipts"
        constraints = [
            models.UniqueConstraint(
                fields=["message_id", "user"],
                name="uq_chat_receipt_message_user",
            )
        ]
        indexes = [
            models.Index(fields=["user", "read_at"]),
        ]
