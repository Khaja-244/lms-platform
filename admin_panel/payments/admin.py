from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "subscription",
        "amount",
        "payment_method",
        "payment_status",
        "transaction_id",
        "invoice_number",
        "paid_at",
    )

    list_filter = (
        "payment_status",
        "payment_method",
        "paid_at",
    )

    search_fields = (
        "transaction_id",
        "invoice_number",
        "subscription__user__email",
    )

    ordering = (
        "-paid_at",
    )

    readonly_fields = (
        "paid_at",
        "created_at",
        "updated_at",
    )

    list_per_page = 10