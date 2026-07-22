from django.contrib import admin

from .models import ActivityLog, AnalyticsRecord, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "title", "notification_type", "is_read", "email_sent", "created_at")
    list_filter = ("notification_type", "is_read", "email_sent", "created_at")
    search_fields = ("user__email", "user__name", "title", "message")
    readonly_fields = ("created_at",)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("user", "action_type", "ip_address", "created_at")
    list_filter = ("action_type", "created_at")
    search_fields = ("user__email", "user__name", "action_detail")
    readonly_fields = ("created_at",)


@admin.register(AnalyticsRecord)
class AnalyticsRecordAdmin(admin.ModelAdmin):
    list_display = ("date", "total_users", "active_subscriptions", "revenue", "popular_course")
    list_filter = ("date",)
    search_fields = ("popular_course__title",)
