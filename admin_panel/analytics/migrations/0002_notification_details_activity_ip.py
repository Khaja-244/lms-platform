from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analytics", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="title",
            field=models.CharField(default="Platform Notification", max_length=160),
        ),
        migrations.AddField(
            model_name="notification",
            name="icon",
            field=models.CharField(default="bi-bell", max_length=40),
        ),
        migrations.AddField(
            model_name="notification",
            name="link",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="activitylog",
            name="ip_address",
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="notification",
            name="notification_type",
            field=models.CharField(
                choices=[
                    ("welcome_registration", "Welcome Registration"),
                    ("payment_success", "Payment Success"),
                    ("payment_failed", "Payment Failed"),
                    ("subscription_activated", "Subscription Activated"),
                    ("subscription_renewed", "Subscription Renewed"),
                    ("subscription_expiring", "Subscription Expiring"),
                    ("subscription_expired", "Subscription Expired"),
                    ("course_purchased", "Course Purchased"),
                    ("course_enrolled", "Course Enrolled"),
                    ("plan_expiry", "Plan Expiry"),
                    ("course_update", "Course Update"),
                    ("new_lesson_published", "New Lesson Published"),
                    ("password_changed", "Password Changed"),
                    ("instructor_message", "Instructor Message"),
                    ("admin_broadcast", "Admin Broadcast"),
                    ("system", "System"),
                ],
                default="system",
                max_length=40,
            ),
        ),
    ]
