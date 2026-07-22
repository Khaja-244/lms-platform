# Generated manually for lesson ZIP resource validation.

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0003_course_duration_course_level_course_thumbnail_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="lesson",
            name="resources",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="lesson_resources/",
                validators=[django.core.validators.FileExtensionValidator(["zip"])],
            ),
        ),
    ]

