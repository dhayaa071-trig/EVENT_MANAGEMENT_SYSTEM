from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Event, Registration


class RegistrationManagementTests(TestCase):
    def setUp(self):
        self.organizer = User.objects.create_user(
            username="organizer",
            password="test-password-123",
        )
        self.staff = User.objects.create_user(
            username="staff",
            password="test-password-123",
            is_staff=True,
        )
        self.attendee = User.objects.create_user(
            username="attendee",
            email="attendee@example.com",
            password="test-password-123",
        )
        self.event = Event.objects.create(
            organizer=self.organizer,
            title="Community Picnic",
            description="A relaxed afternoon together.",
            starts_at=timezone.now() + timedelta(days=5),
            location="Riverside Park",
            capacity=2,
            whatsapp_group_url="https://chat.whatsapp.com/exampleinvite",
        )

    def registration_payload(self):
        return {
            "full_name": "Attendee Example",
            "phone": "+15551234567",
            "organization": "Gather Club",
            "attendee_note": "Vegetarian meal, please.",
        }

    def test_new_event_registration_waits_for_staff_approval(self):
        self.client.force_login(self.attendee)

        response = self.client.post(
            reverse("event_register", args=[self.event.slug]),
            self.registration_payload(),
        )

        self.assertRedirects(response, reverse("event_detail", args=[self.event.slug]))
        registration = Registration.objects.get(event=self.event, attendee=self.attendee)
        self.assertEqual(registration.status, Registration.STATUS_PENDING)
        self.assertEqual(registration.full_name, "Attendee Example")
        self.assertEqual(registration.phone, "+15551234567")

    def test_staff_can_accept_registration(self):
        registration = Registration.objects.create(
            event=self.event,
            attendee=self.attendee,
            full_name="Attendee Example",
            phone="+15551234567",
        )
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("review_registration", args=[registration.pk]),
            {"status": Registration.STATUS_ACCEPTED},
        )

        registration.refresh_from_db()
        self.assertRedirects(response, reverse("staff_dashboard"))
        self.assertEqual(registration.status, Registration.STATUS_ACCEPTED)
        self.assertEqual(registration.reviewed_by, self.staff)
        self.assertIsNotNone(registration.reviewed_at)

    def test_staff_can_reject_registration_and_free_the_reserved_spot(self):
        registration = Registration.objects.create(
            event=self.event,
            attendee=self.attendee,
            full_name="Attendee Example",
            phone="+15551234567",
        )
        self.client.force_login(self.staff)

        self.client.post(
            reverse("review_registration", args=[registration.pk]),
            {"status": Registration.STATUS_REJECTED},
        )

        registration.refresh_from_db()
        self.assertEqual(registration.status, Registration.STATUS_REJECTED)
        self.assertEqual(self.event.spots_left, self.event.capacity)

    def test_non_staff_cannot_open_staff_dashboard(self):
        self.client.force_login(self.attendee)

        response = self.client.get(reverse("staff_dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_whatsapp_invite_is_only_shown_to_accepted_attendee(self):
        registration = Registration.objects.create(
            event=self.event,
            attendee=self.attendee,
            full_name="Attendee Example",
            phone="+15551234567",
        )
        self.client.force_login(self.attendee)

        pending_response = self.client.get(reverse("event_detail", args=[self.event.slug]))
        self.assertNotContains(pending_response, self.event.whatsapp_group_url)

        registration.status = Registration.STATUS_ACCEPTED
        registration.save(update_fields=["status"])
        accepted_response = self.client.get(reverse("event_detail", args=[self.event.slug]))
        self.assertContains(accepted_response, self.event.whatsapp_group_url)

    def test_rejected_attendee_can_request_a_spot_again(self):
        Registration.objects.create(
            event=self.event,
            attendee=self.attendee,
            full_name="Attendee Example",
            phone="+15551234567",
            status=Registration.STATUS_REJECTED,
        )
        self.client.force_login(self.attendee)

        self.client.post(
            reverse("event_register", args=[self.event.slug]),
            self.registration_payload(),
        )

        registration = Registration.objects.get(event=self.event, attendee=self.attendee)
        self.assertEqual(registration.status, Registration.STATUS_PENDING)
        self.assertIsNone(registration.reviewed_by)

    def test_staff_can_open_online_attendance_sheet_and_download_pdf(self):
        Registration.objects.create(
            event=self.event,
            attendee=self.attendee,
            full_name="Attendee Example",
            phone="+15551234567",
            status=Registration.STATUS_ACCEPTED,
        )
        self.client.force_login(self.staff)

        online_response = self.client.get(
            reverse("staff_event_detail", args=[self.event.pk])
        )
        pdf_response = self.client.get(reverse("attendance_pdf", args=[self.event.pk]))

        self.assertContains(online_response, "Attendee Example")
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertTrue(pdf_response.content.startswith(b"%PDF"))

    def test_staff_can_post_announcement_visible_to_accepted_attendee(self):
        Registration.objects.create(
            event=self.event,
            attendee=self.attendee,
            full_name="Attendee Example",
            phone="+15551234567",
            status=Registration.STATUS_ACCEPTED,
        )
        self.client.force_login(self.staff)

        response = self.client.post(
            reverse("staff_announcement_create", args=[self.event.pk]),
            {"title": "Meeting point", "message": "Meet by the main entrance."},
        )

        self.assertRedirects(
            response,
            reverse("staff_event_detail", args=[self.event.pk]),
        )
        self.client.force_login(self.attendee)
        event_response = self.client.get(reverse("event_detail", args=[self.event.slug]))
        self.assertContains(event_response, "Meet by the main entrance.")

    def test_staff_check_in_requires_accepted_registration(self):
        registration = Registration.objects.create(
            event=self.event,
            attendee=self.attendee,
            full_name="Attendee Example",
            phone="+15551234567",
        )
        self.client.force_login(self.staff)

        self.client.post(
            reverse("attendance_update", args=[registration.pk]),
            {"attended": "true"},
        )

        registration.refresh_from_db()
        self.assertFalse(registration.attended)
        self.assertIsNone(registration.checked_in_at)

    def test_staff_can_check_in_accepted_attendee(self):
        registration = Registration.objects.create(
            event=self.event,
            attendee=self.attendee,
            full_name="Attendee Example",
            phone="+15551234567",
            status=Registration.STATUS_ACCEPTED,
        )
        self.client.force_login(self.staff)

        self.client.post(
            reverse("attendance_update", args=[registration.pk]),
            {"attended": "true"},
        )

        registration.refresh_from_db()
        self.assertTrue(registration.attended)
        self.assertIsNotNone(registration.checked_in_at)