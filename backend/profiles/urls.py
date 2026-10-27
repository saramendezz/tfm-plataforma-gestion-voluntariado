from django.urls import path

from .views import MyOrganizationProfileView, MyVolunteerProfileView, SkillListView

urlpatterns = [
    path("skills/", SkillListView.as_view()),
    path("profiles/volunteer/me/", MyVolunteerProfileView.as_view()),
    path("profiles/organization/me/", MyOrganizationProfileView.as_view()),
]