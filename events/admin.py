from django.contrib import admin

from .models import Announcement, Event, Registration


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "starts_at", "location", "organizer", "capacity")
    list_filter = ("category", "starts_at")
    search_fields = ("title", "location", "organizer__username")


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "full_name",
        "attendee",
        "phone",
        "status",
        "attended",
        "registered_at",
    )
    list_filter = ("status", "attended", "event")
    search_fields = (
        "event__title",
        "full_name",
        "phone",
        "organization",
        "attendee__username",
        "attendee__email",
    )
    readonly_fields = ("registered_at", "reviewed_at", "checked_in_at")


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "event", "created_by", "created_at")
    list_filter = ("event", "created_at")
    search_fields = ("title", "message", "event__title")