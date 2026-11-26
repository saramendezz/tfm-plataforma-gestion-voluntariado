from django.urls import path

from .views import CompatibleNeedsView, NeedPotentialView

urlpatterns = [
    path("needs/compatible/", CompatibleNeedsView.as_view()),
    path("needs/<int:pk>/potential/", NeedPotentialView.as_view()),
]