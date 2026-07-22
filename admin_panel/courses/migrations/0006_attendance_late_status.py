from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("courses", "0005_attendance_assignment_submission")]
    operations = [
        migrations.AlterField(
            model_name="attendance",
            name="status",
            field=models.CharField(choices=[("Present", "Present"), ("Absent", "Absent"), ("Late", "Late")], max_length=10),
        ),
    ]
