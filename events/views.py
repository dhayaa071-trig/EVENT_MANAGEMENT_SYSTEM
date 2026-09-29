from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from xml.sax.saxutils import escape

from .forms import AnnouncementForm, EventForm, EventGroupForm, RegistrationForm, SignUpForm
from .models import Announcement, Event, Registration


class StaffLoginView(LoginView):
    template_name = "events/login.html"

    def get_success_url(self):
        redirect_to = self.get_redirect_url()
        if redirect_to:
            return redirect_to
        if self.request.user.is_staff:
            return reverse("staff_dashboard")
        return reverse("dashboard")


def home(request):
    events = Event.objects.filter(starts_at__gt=timezone.now()).select_related("organizer")
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    if query:
        events = events.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(location__icontains=query)
        )
    if category in dict(Event.CATEGORIES):
        events = events.filter(category=category)
    return render(
        request,
        "events/home.html",
        {"events": events, "query": query, "categories": Event.CATEGORIES, "category": category},
    )


def event_detail(request, slug):
    event = get_object_or_404(Event.objects.select_related("organizer"), slug=slug)
    registration = None
    if request.user.is_authenticated:
        registration = event.registrations.filter(attendee=request.user).first()
    announcements = event.announcements.all()
    if not (request.user.is_staff or (registration and registration.status == Registration.STATUS_ACCEPTED)):
        announcements = announcements.none()
    return render(
        request,
        "events/detail.html",
        {"event": event, "registration": registration, "announcements": announcements},
    )


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account is ready. Welcome to Gather!")
        return redirect("dashboard")
    return render(request, "events/signup.html", {"form": form})


@login_required
def dashboard(request):
    hosted = Event.objects.filter(organizer=request.user)
    attending = Registration.objects.filter(
        attendee=request.user, event__starts_at__gt=timezone.now()
    ).select_related("event")
    return render(request, "events/dashboard.html", {"hosted": hosted, "attending": attending})


@login_required
def event_create(request):
    form = EventForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        event = form.save(commit=False)
        event.organizer = request.user
        event.save()
        messages.success(request, "Your event is live.")
        return redirect("event_detail", slug=event.slug)
    return render(request, "events/event_form.html", {"form": form})


@login_required
def event_register(request, slug):
    registration = Registration.objects.filter(event__slug=slug, attendee=request.user).first()
    form = RegistrationForm(request.POST or None, instance=registration)
    if request.method != "POST":
        return render(
            request,
            "events/registration_form.html",
            {"event": get_object_or_404(Event, slug=slug), "form": form},
        )
    if not form.is_valid():
        return render(
            request,
            "events/registration_form.html",
            {"event": get_object_or_404(Event, slug=slug), "form": form},
            status=400,
        )
    with transaction.atomic():
        event = get_object_or_404(Event.objects.select_for_update(), slug=slug)
        if not event.is_upcoming:
            messages.error(request, "This event has already taken place.")
        else:
            existing = Registration.objects.filter(
                event=event,
                attendee=request.user,
            ).first()
            if existing and existing.status != Registration.STATUS_REJECTED:
                messages.info(request, "Your registration is already being processed.")
            elif event.spots_left <= 0:
                messages.error(request, "Sorry, this event is full.")
            elif existing:
                existing.full_name = form.cleaned_data["full_name"]
                existing.phone = form.cleaned_data["phone"]
                existing.organization = form.cleaned_data["organization"]
                existing.attendee_note = form.cleaned_data["attendee_note"]
                existing.status = Registration.STATUS_PENDING
                existing.reviewed_by = None
                existing.reviewed_at = None
                existing.save()
                messages.success(request, "Your registration has been sent for review again.")
            else:
                new_registration = form.save(commit=False)
                new_registration.event = event
                new_registration.attendee = request.user
                new_registration.save()
                messages.success(request, "Your registration has been sent for review.")
    return redirect("event_detail", slug=slug)


@user_passes_test(lambda user: user.is_active and user.is_staff)
def staff_dashboard(request):
    registrations = Registration.objects.select_related(
        "event",
        "attendee",
        "reviewed_by",
    )
    event_id = request.GET.get("event", "").strip()
    status = request.GET.get("status", "").strip()
    if event_id.isdigit():
        registrations = registrations.filter(event_id=int(event_id))
    if status in dict(Registration.STATUS_CHOICES):
        registrations = registrations.filter(status=status)
    events = Event.objects.annotate(registration_count=Count("registrations"))
    return render(
        request,
        "events/staff_dashboard.html",
        {
            "registrations": registrations,
            "events": events,
            "selected_event": event_id,
            "selected_status": status,
            "statuses": Registration.STATUS_CHOICES,
            "staff_events": events,
        },
    )


@user_passes_test(lambda user: user.is_active and user.is_staff)
def staff_event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    registrations = event.registrations.select_related("attendee", "reviewed_by")
    announcement_form = AnnouncementForm()
    group_form = EventGroupForm(instance=event)
    return render(
        request,
        "events/staff_event_detail.html",
        {
            "event": event,
            "registrations": registrations,
            "announcement_form": announcement_form,
            "group_form": group_form,
            "announcements": event.announcements.all(),
        },
    )


@user_passes_test(lambda user: user.is_active and user.is_staff)
@require_POST
def staff_announcement_create(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    form = AnnouncementForm(request.POST)
    if form.is_valid():
        announcement = form.save(commit=False)
        announcement.event = event
        announcement.created_by = request.user
        announcement.save()
        messages.success(request, "Announcement posted for accepted attendees.")
    else:
        messages.error(request, "Add an announcement title and message.")
    return redirect("staff_event_detail", event_id=event.pk)


@user_passes_test(lambda user: user.is_active and user.is_staff)
@require_POST
def staff_announcement_delete(request, announcement_id):
    announcement = get_object_or_404(
        Announcement.objects.select_related("event"),
        pk=announcement_id,
    )
    event_id = announcement.event_id
    announcement.delete()
    messages.success(request, "Announcement deleted.")
    return redirect("staff_event_detail", event_id=event_id)


@user_passes_test(lambda user: user.is_active and user.is_staff)
@require_POST
def staff_group_link_update(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    form = EventGroupForm(request.POST, instance=event)
    if form.is_valid():
        form.save()
        messages.success(request, "WhatsApp invite link updated.")
    else:
        messages.error(request, "Enter a valid WhatsApp invite URL.")
    return redirect("staff_event_detail", event_id=event.pk)


@user_passes_test(lambda user: user.is_active and user.is_staff)
@require_POST
def attendance_update(request, registration_id):
    registration = get_object_or_404(
        Registration.objects.select_related("event"),
        pk=registration_id,
    )
    if registration.status != Registration.STATUS_ACCEPTED:
        messages.error(request, "Only accepted attendees can be checked in.")
    else:
        attended = request.POST.get("attended") == "true"
        registration.attended = attended
        registration.checked_in_at = timezone.now() if attended else None
        registration.save(update_fields=["attended", "checked_in_at"])
        messages.success(
            request,
            f"Attendance updated for {registration.full_name}.",
        )
    return redirect("staff_event_detail", event_id=registration.event_id)


@user_passes_test(lambda user: user.is_active and user.is_staff)
def attendance_pdf(request, event_id):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph

    event = get_object_or_404(Event, pk=event_id)
    registrations = event.registrations.filter(
        status=Registration.STATUS_ACCEPTED
    ).select_related("attendee")
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="attendance-{event.slug}.pdf"'
    )
    document = SimpleDocTemplate(response, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    rows = [["Name", "Username", "Email", "Phone", "Organization", "Attended", "Check-in"]]
    rows.extend(
        [
            [
                _pdf_text(registration.full_name),
                _pdf_text(registration.attendee.username),
                _pdf_text(registration.attendee.email or ""),
                _pdf_text(registration.phone),
                _pdf_text(registration.organization),
                "Yes" if registration.attended else "No",
                timezone.localtime(registration.checked_in_at).strftime("%Y-%m-%d %H:%M")
                if registration.checked_in_at
                else "",
            ]
            for registration in registrations
        ]
    )
    table = Table(
        rows,
        colWidths=[118, 68, 126, 78, 112, 54, 83],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#282722")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d8d4cb")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f5ef")]),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    document.build(
        [
            Paragraph(f"Attendance sheet - {escape(_pdf_text(event.title))}", styles["Title"]),
            Paragraph(
                f"{event.starts_at:%A, %B %d, %Y at %I:%M %p} - {escape(_pdf_text(event.location))}",
                styles["Normal"],
            ),
            Spacer(1, 16),
            table,
        ]
    )
    return response


def _pdf_text(value):
    return str(value).encode("latin-1", errors="replace").decode("latin-1")


@user_passes_test(lambda user: user.is_active and user.is_staff)
@require_POST
def review_registration(request, registration_id):
    status = request.POST.get("status")
    if status not in {Registration.STATUS_ACCEPTED, Registration.STATUS_REJECTED}:
        messages.error(request, "Choose whether to accept or reject this registration.")
        return _staff_review_redirect(request)

    registration = get_object_or_404(
        Registration.objects.select_related("event"),
        pk=registration_id,
    )
    if status == Registration.STATUS_ACCEPTED:
        reserved_by_others = registration.event.registrations.exclude(
            status=Registration.STATUS_REJECTED
        ).exclude(pk=registration.pk).count()
        if reserved_by_others >= registration.event.capacity:
            messages.error(
                request,
                f"{registration.event.title} has no unreserved places. Reject other pending requests or increase capacity first.",
            )
            return _staff_review_redirect(request)

    registration.status = status
    registration.reviewed_by = request.user
    registration.reviewed_at = timezone.now()
    registration.save(update_fields=["status", "reviewed_by", "reviewed_at"])
    messages.success(
        request,
        f"{registration.attendee.username}'s registration was {status}.",
    )
    return _staff_review_redirect(request)


def _staff_review_redirect(request):
    target = request.POST.get("next", "")
    if target and url_has_allowed_host_and_scheme(
        target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(target)
    return redirect("staff_dashboard")