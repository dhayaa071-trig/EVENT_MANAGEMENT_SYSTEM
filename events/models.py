from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Event(models.Model):
    CATEGORIES = [
        ("Community", "Community"),
        ("Music", "Music"),
        ("Food & Drink", "Food & Drink"),
        ("Learning", "Learning"),
        ("Arts & Culture", "Arts & Culture"),
        ("Other", "Other"),
    ]
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organized_events",
    )
    title = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, blank=True)
    category = models.CharField(max_length=30, choices=CATEGORIES, default="Community")
    description = models.TextField(max_length=3000)
    starts_at = models.DateTimeField()
    location = models.CharField(max_length=180)
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    whatsapp_group_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["starts_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title) or "event"
            slug = base
            count = 2
            while Event.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{count}"
                count += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def spots_left(self):
        active_registrations = self.registrations.exclude(status="rejected").count()
        return max(self.capacity - active_registrations, 0)

    @property
    def is_upcoming(self):
        return self.starts_at > timezone.now()

    def __str__(self):
        return self.title


class Registration(models.Model):
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_REJECTED, "Rejected"),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="registrations")
    attendee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_registrations",
    )
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    organization = models.CharField(max_length=120, blank=True)
    attendee_note = models.TextField(max_length=500, blank=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_event_registrations",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "attendee"],
                name="unique_event_registration",
            )
        ]

    def __str__(self):
        return f"{self.attendee} — {self.event}"


class Announcement(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="announcements")
    title = models.CharField(max_length=120)
    message = models.TextField(max_length=3000)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="event_announcements",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event}: {self.title}"