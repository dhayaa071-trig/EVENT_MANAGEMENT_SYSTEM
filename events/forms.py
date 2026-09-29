from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Announcement, Event, Registration


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")


class EventForm(forms.ModelForm):
    starts_at = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M"],
        widget=forms.DateTimeInput(
            format="%Y-%m-%dT%H:%M",
            attrs={"type": "datetime-local"},
        ),
    )

    class Meta:
        model = Event
        fields = (
            "title",
            "category",
            "description",
            "starts_at",
            "location",
            "capacity",
            "whatsapp_group_url",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "whatsapp_group_url": forms.URLInput(
                attrs={"placeholder": "https://chat.whatsapp.com/..."}
            ),
        }
        help_texts = {
            "whatsapp_group_url": (
                "Optional. Accepted attendees will see this invite link on the event page."
            )
        }

    def clean_starts_at(self):
        starts_at = self.cleaned_data["starts_at"]
        if starts_at <= timezone.now():
            raise forms.ValidationError("Choose a date and time in the future.")
        return starts_at


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ("full_name", "phone", "organization", "attendee_note")
        labels = {
            "full_name": "Full name",
            "phone": "Phone number",
            "organization": "Organization / affiliation (optional)",
            "attendee_note": "Additional information (optional)",
        }
        help_texts = {
            "attendee_note": "Share relevant attendee details only. Do not enter government ID numbers.",
        }
        widgets = {"attendee_note": forms.Textarea(attrs={"rows": 3})}


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ("title", "message")
        widgets = {"message": forms.Textarea(attrs={"rows": 4})}


class EventGroupForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ("whatsapp_group_url",)
        widgets = {
            "whatsapp_group_url": forms.URLInput(
                attrs={"placeholder": "https://chat.whatsapp.com/..."}
            )
        }
        help_texts = {
            "whatsapp_group_url": (
                "Accepted attendees can see this invite and choose to join. "
                "The site cannot add members to WhatsApp automatically."
            )
        }