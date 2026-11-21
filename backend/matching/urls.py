from django.urls import path

from .views import CompatibleNeedsView, NeedCandidatesView

urlpatterns = [
    path("needs/compatible/", CompatibleNeedsView.as_view()),
    path("needs/<int:pk>/candidates/", NeedCandidatesView.as_view()),
]