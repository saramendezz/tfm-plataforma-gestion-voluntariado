from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsVerifiedOrganization, IsVolunteer
from needs.models import Need
from participations.models import Participation
from profiles.models import VolunteerProfile

from .services import evaluate, load_coordinates


class NeedPotentialView(APIView):
    """Número de voluntarios compatibles con una necesidad, sin datos identificativos."""

    permission_classes = [IsVerifiedOrganization]

    def get(self, request, pk):
        need = get_object_or_404(
            Need.objects.prefetch_related("required_skills"),
            pk=pk,
            organization=request.user.organization_profile,
        )
        volunteers = list(
            VolunteerProfile.objects.filter(is_available=True).prefetch_related(
                "skills", "availability_slots"
            )
        )
        coordinates = load_coordinates(
            [need.postal_code] + [v.postal_code for v in volunteers]
        )
        potential = sum(1 for v in volunteers if evaluate(v, need, coordinates))
        confirmed = need.participations.filter(
            status=Participation.Status.CONFIRMED
        ).count()
        return Response(
            {
                "need_id": need.id,
                "volunteers_needed": need.volunteers_needed,
                "confirmed": confirmed,
                "potential_volunteers": potential,
            }
        )


class CompatibleNeedsView(APIView):
    """Necesidades compatibles con el voluntario a las que puede apuntarse."""

    permission_classes = [IsVolunteer]

    def get(self, request):
        volunteer = (
            VolunteerProfile.objects.filter(user=request.user)
            .prefetch_related("skills", "availability_slots")
            .first()
        )
        if volunteer is None:
            return Response([])

        confirmed = Participation.objects.filter(
            volunteer=volunteer, status=Participation.Status.CONFIRMED
        )
        mine = dict(confirmed.values_list("need_id", "id"))
        busy = list(confirmed.values_list("need__start_at", "need__end_at"))
        removed = set(
            Participation.objects.filter(
                volunteer=volunteer, status=Participation.Status.REMOVED
            ).values_list("need_id", flat=True)
        )

        needs = list(
            Need.objects.filter(
                status=Need.Status.OPEN,
                organization__is_verified=True,
                start_at__gt=timezone.now(),
            )
            .annotate(
                confirmed_count=Count(
                    "participations",
                    filter=Q(participations__status=Participation.Status.CONFIRMED),
                )
            )
            .select_related("organization")
            .prefetch_related("required_skills")
        )

        def available(need):
            if need.id in mine:
                return True
            if need.id in removed:
                return False
            if need.confirmed_count >= need.volunteers_needed:
                return False
            return not any(s < need.end_at and e > need.start_at for s, e in busy)

        needs = [n for n in needs if available(n)]
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
                        "spots_left": need.volunteers_needed - need.confirmed_count,
                        "participation_id": mine.get(need.id),
                        **match.as_dict(),
                    }
                )
        results.sort(key=lambda r: (-r["score"], r["distance_km"]))
        return Response(results)