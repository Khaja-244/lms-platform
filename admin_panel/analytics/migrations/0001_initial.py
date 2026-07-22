from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("courses", "0004_alter_lesson_resources"),
    ]

    operations = [
        migrations.CreateModel(
            name="AnalyticsRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(unique=True)),
                ("total_users", models.PositiveIntegerField(default=0)),
                ("active_subscriptions", models.PositiveIntegerField(default=0)),
                ("revenue", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "popular_course",
                    models.ForeignKey(
                        blank=True,
                        db_column="popular_course_id",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="analytics_records",
                        to="courses.course",
                    ),
                ),
            ],
            options={
                "db_table": "analytics_records",
                "ordering": ["-date"],
            },
        ),
        migrations.CreateModel(
            name="ActivityLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action_type", models.CharField(max_length=80)),
                ("action_detail", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "user",
                    models.ForeignKey(
                        db_column="user_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="activity_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "activity_logs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("message", models.TextField()),
                ("notification_type", models.CharField(choices=[("plan_expiry", "Plan Expiry"), ("course_update", "Course Update"), ("instructor_message", "Instructor Message"), ("system", "System")], default="system", max_length=40)),
                ("is_read", models.BooleanField(default=False)),
                ("email_sent", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "user",
                    models.ForeignKey(
                        db_column="user_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "notifications",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="activitylog",
            index=models.Index(fields=["user", "created_at"], name="activity_l_user_id_2e8d21_idx"),
        ),
        migrations.AddIndex(
            model_name="activitylog",
            index=models.Index(fields=["action_type"], name="activity_l_action__c80302_idx"),
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(fields=["user", "is_read"], name="notificatio_user_id_4d65c1_idx"),
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(fields=["created_at"], name="notificatio_created_4964ad_idx"),
        ),
    ]
