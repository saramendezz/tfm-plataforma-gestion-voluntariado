from django.urls import path

from .views import (
    MyAvailabilityDetailView,
    MyAvailabilityView,
    MyOrganizationProfileView,
    MyVolunteerProfileView,
    SkillListView,
)

urlpatterns = [
    path("skills/", SkillListView.as_view()),
    path("profiles/volunteer/me/", MyVolunteerProfileView.as_view()),
    path("profiles/organization/me/", MyOrganizationProfileView.as_view()),
    path("availability/", MyAvailabilityView.as_view()),
    path("availability/<int:pk>/", MyAvailabilityDetailView.as_view()),
]