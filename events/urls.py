from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.StaffLoginView.as_view(), name="login"),
    path("staff/login/", views.StaffLoginView.as_view(), name="staff_login"),
    path("staff/", views.staff_dashboard, name="staff_dashboard"),
    path(
        "staff/registrations/<int:registration_id>/review/",
        views.review_registration,
        name="review_registration",
    ),
    path(
        "staff/events/<int:event_id>/",
        views.staff_event_detail,
        name="staff_event_detail",
    ),
    path(
        "staff/events/<int:event_id>/announcement/",
        views.staff_announcement_create,
        name="staff_announcement_create",
    ),
    path(
        "staff/announcements/<int:announcement_id>/delete/",
        views.staff_announcement_delete,
        name="staff_announcement_delete",
    ),
    path(
        "staff/events/<int:event_id>/group-link/",
        views.staff_group_link_update,
        name="staff_group_link_update",
    ),
    path(
        "staff/registrations/<int:registration_id>/attendance/",
        views.attendance_update,
        name="attendance_update",
    ),
    path(
        "staff/events/<int:event_id>/attendance.pdf",
        views.attendance_pdf,
        name="attendance_pdf",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("events/create/", views.event_create, name="event_create"),
    path("events/<slug:slug>/", views.event_detail, name="event_detail"),
    path("events/<slug:slug>/register/", views.event_register, name="event_register"),
]