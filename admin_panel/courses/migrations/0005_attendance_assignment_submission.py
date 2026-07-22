from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("courses", "0004_alter_lesson_resources"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="Assignment", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("title", models.CharField(max_length=200)), ("description", models.TextField(blank=True)),
            ("deadline", models.DateTimeField()), ("file_url", models.CharField(blank=True, max_length=500)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("course", models.ForeignKey(db_column="course_id", on_delete=django.db.models.deletion.CASCADE, related_name="assignments", to="courses.course")),
            ("created_by", models.ForeignKey(db_column="created_by", on_delete=django.db.models.deletion.PROTECT, related_name="assignments_created", to=settings.AUTH_USER_MODEL)),
        ], options={"db_table": "assignments", "ordering": ["deadline"]}),
        migrations.CreateModel(name="Attendance", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("date", models.DateField()), ("status", models.CharField(choices=[("Present", "Present"), ("Absent", "Absent")], max_length=10)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("course", models.ForeignKey(db_column="course_id", on_delete=django.db.models.deletion.CASCADE, related_name="attendance_records", to="courses.course")),
            ("marked_by", models.ForeignKey(db_column="marked_by", on_delete=django.db.models.deletion.PROTECT, related_name="attendance_marked", to=settings.AUTH_USER_MODEL)),
            ("student", models.ForeignKey(db_column="student_id", on_delete=django.db.models.deletion.CASCADE, related_name="attendance_records", to=settings.AUTH_USER_MODEL)),
        ], options={"db_table": "attendance", "ordering": ["-date", "student_id"]}),
        migrations.CreateModel(name="Submission", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("file_url", models.CharField(max_length=500)), ("original_filename", models.CharField(max_length=255)),
            ("submitted_at", models.DateTimeField(auto_now_add=True)), ("grade", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
            ("remarks", models.TextField(blank=True)), ("graded_at", models.DateTimeField(blank=True, null=True)),
            ("assignment", models.ForeignKey(db_column="assignment_id", on_delete=django.db.models.deletion.CASCADE, related_name="submissions", to="courses.assignment")),
            ("graded_by", models.ForeignKey(blank=True, db_column="graded_by", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="submissions_graded", to=settings.AUTH_USER_MODEL)),
            ("student", models.ForeignKey(db_column="student_id", on_delete=django.db.models.deletion.CASCADE, related_name="assignment_submissions", to=settings.AUTH_USER_MODEL)),
        ], options={"db_table": "submissions", "ordering": ["-submitted_at"]}),
        migrations.AddConstraint(model_name="attendance", constraint=models.UniqueConstraint(fields=("student", "course", "date"), name="uq_attendance_student_course_date")),
        migrations.AddConstraint(model_name="submission", constraint=models.UniqueConstraint(fields=("assignment", "student"), name="uq_submission_assignment_student")),
        migrations.AddIndex(model_name="attendance", index=models.Index(fields=["course", "date"], name="attendance_course_date_idx")),
        migrations.AddIndex(model_name="attendance", index=models.Index(fields=["student", "course"], name="attendance_student_course_idx")),
        migrations.AddIndex(model_name="assignment", index=models.Index(fields=["course", "deadline"], name="assignment_course_deadline_idx")),
        migrations.AddIndex(model_name="submission", index=models.Index(fields=["assignment", "student"], name="submission_asgn_student_idx")),
    ]
