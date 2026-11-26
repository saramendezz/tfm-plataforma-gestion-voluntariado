from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsVerifiedOrganization, IsVolunteer
from needs.models import Need
from profiles.models import VolunteerProfile

from .models import Participation
from .services import ParticipationError, accept, remove, withdraw


def participation_payload(p):
    need = p.need
    return {
        "id": p.id,
        "status": p.status,
        "accepted_at": p.created_at,
        "ended_at": p.ended_at,
        "need": {
            "id": need.id,
            "title": need.title,
            "organization_name": need.organization.name,
            "municipality": need.municipality,
            "province": need.province,
            "start_at": need.start_at,
            "end_at": need.end_at,
        },
        "can_withdraw": p.status == Participation.Status.CONFIRMED
        and need.start_at > timezone.now(),
    }


class AcceptView(APIView):
    permission_classes = [IsVolunteer]

    def post(self, request, pk):
        volunteer, _ = VolunteerProfile.objects.get_or_create(user=request.user)
        need = get_object_or_404(Need, pk=pk, organization__is_verified=True)
        try:
            participation = accept(volunteer, need)
        except ParticipationError as exc:
            raise ValidationError(str(exc))
        return Response(participation_payload(participation), status=201)


class MyParticipationsView(APIView):
    permission_classes = [IsVolunteer]

    def get(self, request):
        participations = Participation.objects.filter(
            volunteer__user=request.user
        ).select_related("need__organization")
        return Response([participation_payload(p) for p in participations])


class WithdrawView(APIView):
    permission_classes = [IsVolunteer]

    def post(self, request, pk):
        participation = get_object_or_404(
            Participation.objects.select_related("need__organization"),
            pk=pk,
            volunteer__user=request.user,
        )
        try:
            withdraw(participation)
        except ParticipationError as exc:
            raise ValidationError(str(exc))
        return Response(participation_payload(participation))


class NeedParticipantsView(APIView):
    """Voluntarios que han aceptado: aquí sí se muestran identidad y contacto."""

    permission_classes = [IsVerifiedOrganization]

    def get(self, request, pk):
        need = get_object_or_404(
            Need, pk=pk, organization=request.user.organization_profile
        )
        participations = (
            need.participations.filter(status=Participation.Status.CONFIRMED)
            .select_related("volunteer__user")
            .prefetch_related("volunteer__skills")
            .order_by("created_at")
        )
        return Response(
            [
                {
                    "participation_id": p.id,
                    "username": p.volunteer.user.username,
                    "email": p.volunteer.user.email,
                    "phone": p.volunteer.phone,
                    "municipality": p.volunteer.municipality,
                    "province": p.volunteer.province,
                    "skills": [s.name for s in p.volunteer.skills.all()],
                    "accepted_at": p.created_at,
                }
                for p in participations
            ]
        )


class RemoveView(APIView):
    permission_classes = [IsVerifiedOrganization]

    def post(self, request, pk):
        participation = get_object_or_404(
            Participation.objects.select_related("need__organization"),
            pk=pk,
            need__organization=request.user.organization_profile,
        )
        try:
            remove(participation)
        except ParticipationError as exc:
            raise ValidationError(str(exc))
        return Response({"id": participation.id, "status": participation.status})