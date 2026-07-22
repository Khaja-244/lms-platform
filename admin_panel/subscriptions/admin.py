from django.contrib import admin

from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "plan",
        "status",
        "start_date",
        "end_date",
        "is_active",
    )
    list_filter = (
        "status",
        "plan",
        "start_date",
    )
    search_fields = (
        "user__name",
        "user__email",
        "plan__name",
    )
    ordering = ("-start_date",)
    list_per_page = 10


