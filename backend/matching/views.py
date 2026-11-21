from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsVerifiedOrganization, IsVolunteer
from needs.models import Need
from profiles.models import VolunteerProfile

from .services import evaluate, load_coordinates


class NeedCandidatesView(APIView):
    """Candidatos compatibles con una necesidad de la organización."""

    permission_classes = [IsVerifiedOrganization]

    def get(self, request, pk):
        need = get_object_or_404(
            Need.objects.prefetch_related("required_skills"),
            pk=pk,
            organization=request.user.organization_profile,
        )
        if need.status != Need.Status.OPEN:
            raise ValidationError("La necesidad está cerrada.")

        volunteers = list(
            VolunteerProfile.objects.filter(is_available=True)
            .select_related("user")
            .prefetch_related("skills", "availability_slots")
        )
        coordinates = load_coordinates(
            [need.postal_code] + [v.postal_code for v in volunteers]
        )

        results = []
        for volunteer in volunteers:
            match = evaluate(volunteer, need, coordinates)
            if match:
                results.append(
                    {
                        "volunteer_id": volunteer.id,
                        "username": volunteer.user.username,
                        "municipality": volunteer.municipality,
                        "province": volunteer.province,
                        **match.as_dict(),
                    }
                )
        results.sort(key=lambda r: (-r["score"], r["distance_km"]))
        return Response(results)


class CompatibleNeedsView(APIView):
    """Necesidades abiertas y futuras compatibles con el voluntario."""

    permission_classes = [IsVolunteer]

    def get(self, request):
        volunteer = (
            VolunteerProfile.objects.filter(user=request.user)
            .prefetch_related("skills", "availability_slots")
            .first()
        )
        if volunteer is None:
            return Response([])

        needs = list(
            Need.objects.filter(
                status=Need.Status.OPEN,
                organization__is_verified=True,
                end_at__gt=timezone.now(),
            )
            .select_related("organization")
            .prefetch_related("required_skills")
        )
        coordinates = load_coordinates(
            [volunteer.postal_code] + [n.postal_code for n in needs]
        )

        results = []
        for need in needs:
            match = evaluate(volunteer, need, coordinates)
            if match:
                results.append(
                    {
                        "id": need.id,
                        "title": need.title,
                        "description": need.description,
                        "organization_name": need.organization.name,
                        "municipality": need.municipality,
                        "province": need.province,
                        "start_at": need.start_at,
                        "end_at": need.end_at,
                        "volunteers_needed": need.volunteers_needed,
                        **match.as_dict(),
                    }
                )
        results.sort(key=lambda r: (-r["score"], r["distance_km"]))
        return Response(results)