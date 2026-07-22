from django.db import models
from django.utils import timezone

from subscriptions.models import Subscription


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"
    REFUNDED = "refunded", "Refunded"


class PaymentMethod(models.TextChoices):
    CARD = "card", "Card"
    UPI = "upi", "UPI"
    NETBANKING = "netbanking", "Net Banking"
    WALLET = "wallet", "Wallet"


class Payment(models.Model):
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name="payments",
        db_column="subscription_id",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
        null=True,
        blank=True,
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    transaction_id = models.CharField(
        max_length=120,
        unique=True,
        null=True,
        blank=True,
    )

    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
    )

    paid_at = models.DateTimeField(
        default=timezone.now,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "payments"
        ordering = ["-paid_at"]

    def __str__(self):
        return self.transaction_id

    @property
    def is_successful(self):
        return self.payment_status == PaymentStatus.SUCCESS

    def mark_success(self):
        self.payment_status = PaymentStatus.SUCCESS
        self.save(update_fields=["payment_status"])

    def mark_failed(self):
        self.payment_status = PaymentStatus.FAILED
        self.save(update_fields=["payment_status"])

    def mark_refunded(self):
        self.payment_status = PaymentStatus.REFUNDED
        self.save(update_fields=["payment_status"])