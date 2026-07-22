from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from plans.models import Plan


class SubscriptionStatus(models.TextChoices):
    PENDING = "pending", "Pending Payment"
    ACTIVE = "active", "Active"
    EXPIRED = "expired", "Expired"
    CANCELLED = "cancelled", "Cancelled"


class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        db_column="user_id",
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
        db_column="plan_id",
    )
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
    )
    auto_renew = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subscriptions"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"

    def save(self, *args, **kwargs):
        if self.start_date and self.plan_id and not self.end_date:
            self.end_date = self.start_date + timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        if not self.end_date:
            return False
        return self.status == SubscriptionStatus.ACTIVE and self.end_date >= timezone.now()

    def mark_cancelled(self):
        self.status = SubscriptionStatus.CANCELLED
        self.save(update_fields=["status", "updated_at"])

    def mark_expired(self):
        self.status = SubscriptionStatus.EXPIRED
        self.save(update_fields=["status", "updated_at"])
