import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def populate_course_and_enrollment(apps, schema_editor):
    Enrollment = apps.get_model("onlinecourse", "Enrollment")
    Question = apps.get_model("onlinecourse", "Question")
    Submission = apps.get_model("onlinecourse", "Submission")
    database = schema_editor.connection.alias

    for question in Question.objects.using(database).filter(course__isnull=True).select_related("lesson"):
        question.course_id = question.lesson.course_id
        question.save(using=database, update_fields=["course"])

    for submission in Submission.objects.using(database).filter(enrollment__isnull=True).select_related(
        "question__course"
    ):
        enrollment, _ = Enrollment.objects.using(database).get_or_create(
            user_id=submission.user_id,
            course_id=submission.question.course_id,
        )
        submission.enrollment_id = enrollment.pk
        submission.save(using=database, update_fields=["enrollment"])


class Migration(migrations.Migration):
    dependencies = [
        ("onlinecourse", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="question",
            old_name="prompt",
            new_name="question_text",
        ),
        migrations.RenameField(
            model_name="choice",
            old_name="text",
            new_name="choice_text",
        ),
        migrations.AddField(
            model_name="question",
            name="grade",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="question",
            name="course",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="questions",
                to="onlinecourse.course",
            ),
        ),
        migrations.AlterField(
            model_name="enrollment",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="submission",
            name="enrollment",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="onlinecourse.enrollment",
            ),
        ),
        migrations.AddField(
            model_name="submission",
            name="choices",
            field=models.ManyToManyField(blank=True, to="onlinecourse.choice"),
        ),
        migrations.RunPython(populate_course_and_enrollment, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="question",
            name="course",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="questions",
                to="onlinecourse.course",
            ),
        ),
        migrations.AlterField(
            model_name="submission",
            name="enrollment",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="onlinecourse.enrollment",
            ),
        ),
    ]
