from django.urls import path

from .views import NeedCloseView, NeedDetailView, NeedListCreateView

urlpatterns = [
    path("needs/", NeedListCreateView.as_view()),
    path("needs/<int:pk>/", NeedDetailView.as_view()),
    path("needs/<int:pk>/close/", NeedCloseView.as_view()),
]