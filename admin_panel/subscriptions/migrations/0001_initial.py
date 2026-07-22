# Generated manually to restore the missing subscriptions app.

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("plans", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Subscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("start_date", models.DateTimeField(default=django.utils.timezone.now)),
                ("end_date", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(choices=[("active", "Active"), ("expired", "Expired"), ("cancelled", "Cancelled")], default="active", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("plan", models.ForeignKey(db_column="plan_id", on_delete=django.db.models.deletion.PROTECT, related_name="subscriptions", to="plans.plan")),
                ("user", models.ForeignKey(db_column="user_id", on_delete=django.db.models.deletion.CASCADE, related_name="subscriptions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "subscriptions",
                "ordering": ["-start_date"],
            },
        ),
    ]


