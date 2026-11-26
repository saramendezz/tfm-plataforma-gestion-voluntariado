from django.urls import path

from .views import (
    AcceptView,
    MyParticipationsView,
    NeedParticipantsView,
    RemoveView,
    WithdrawView,
)

urlpatterns = [
    path("needs/<int:pk>/accept/", AcceptView.as_view()),
    path("needs/<int:pk>/participants/", NeedParticipantsView.as_view()),
    path("participations/", MyParticipationsView.as_view()),
    path("participations/<int:pk>/withdraw/", WithdrawView.as_view()),
    path("participations/<int:pk>/remove/", RemoveView.as_view()),
]