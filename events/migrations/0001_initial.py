import django.core.validators
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Event",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120)),
                ("slug", models.SlugField(blank=True, unique=True)),
                ("category", models.CharField(choices=[("Community", "Community"), ("Music", "Music"), ("Food & Drink", "Food & Drink"), ("Learning", "Learning"), ("Arts & Culture", "Arts & Culture"), ("Other", "Other")], default="Community", max_length=30)),
                ("description", models.TextField(max_length=3000)),
                ("starts_at", models.DateTimeField()),
                ("location", models.CharField(max_length=180)),
                ("capacity", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("organizer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="organized_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["starts_at"]},
        ),
        migrations.CreateModel(
            name="Registration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("registered_at", models.DateTimeField(auto_now_add=True)),
                ("attendee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="event_registrations", to=settings.AUTH_USER_MODEL)),
                ("event", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="registrations", to="events.event")),
            ],
        ),
        migrations.AddConstraint(
            model_name="registration",
            constraint=models.UniqueConstraint(fields=("event", "attendee"), name="unique_event_registration"),
        ),
    ]