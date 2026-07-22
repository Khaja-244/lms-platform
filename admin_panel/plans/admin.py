from django.contrib import admin
from .models import Plan


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "price",
        "duration_days",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "description",
    )

    ordering = (
        "price",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    list_per_page = 10

    fieldsets = (
        (
            "Plan Information",
            {
                "fields": (
                    "name",
                    "description",
                    "price",
                    "duration_days",
                    "is_active",
                )
            },
        ),
        (
            "Audit Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )