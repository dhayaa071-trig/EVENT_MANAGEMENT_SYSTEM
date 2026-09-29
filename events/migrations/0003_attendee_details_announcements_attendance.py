from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("events", "0002_registration_review_and_whatsapp"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="registration",
            name="full_name",
            field=models.CharField(default="", max_length=120),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="registration",
            name="phone",
            field=models.CharField(default="", max_length=30),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="registration",
            name="organization",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="registration",
            name="attendee_note",
            field=models.TextField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="registration",
            name="attended",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="registration",
            name="checked_in_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="Announcement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=120)),
                ("message", models.TextField(max_length=3000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="event_announcements",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "event",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="announcements",
                        to="events.event",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
