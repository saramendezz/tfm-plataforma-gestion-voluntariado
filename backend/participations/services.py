from django.db import transaction
from django.utils import timezone

from matching.services import evaluate, load_coordinates
from needs.models import Need
from profiles.models import VolunteerProfile

from .models import Participation


class ParticipationError(Exception):
    pass


def accept(volunteer, need):
    with transaction.atomic():
        need = (
            Need.objects.select_for_update()
            .prefetch_related("required_skills")
            .get(pk=need.pk)
        )
        if need.status != Need.Status.OPEN:
            raise ParticipationError("La necesidad no está abierta.")
        if need.start_at <= timezone.now():
            raise ParticipationError("La necesidad ya ha comenzado.")

        previous = Participation.objects.filter(volunteer=volunteer, need=need)
        if previous.filter(status=Participation.Status.CONFIRMED).exists():
            raise ParticipationError("Ya participas en esta necesidad.")
        if previous.filter(status=Participation.Status.REMOVED).exists():
            raise ParticipationError(
                "La organización ha retirado tu participación en esta necesidad."
            )

        profile = VolunteerProfile.objects.prefetch_related(
            "skills", "availability_slots"
        ).get(pk=volunteer.pk)
        coordinates = load_coordinates([profile.postal_code, need.postal_code])
        if evaluate(profile, need, coordinates) is None:
            raise ParticipationError("Esta necesidad no es compatible con tu perfil.")

        confirmed = need.participations.filter(
            status=Participation.Status.CONFIRMED
        ).count()
        if confirmed >= need.volunteers_needed:
            raise ParticipationError(
                "La necesidad ya tiene todos los voluntarios necesarios."
            )

        overlapping = Participation.objects.filter(
            volunteer=volunteer,
            status=Participation.Status.CONFIRMED,
            need__start_at__lt=need.end_at,
            need__end_at__gt=need.start_at,
        )
        if overlapping.exists():
            raise ParticipationError(
                "Ya participas en otra necesidad que se solapa con esta."
            )

        return Participation.objects.create(volunteer=volunteer, need=need)


def _end(participation, status):
    participation.status = status
    participation.ended_at = timezone.now()
    participation.save(update_fields=["status", "ended_at"])
    return participation


def withdraw(participation):
    if participation.status != Participation.Status.CONFIRMED:
        raise ParticipationError("La participación ya no está activa.")
    if participation.need.start_at <= timezone.now():
        raise ParticipationError("No puedes retirarte: la necesidad ya ha comenzado.")
    return _end(participation, Participation.Status.WITHDRAWN)


def remove(participation):
    if participation.status != Participation.Status.CONFIRMED:
        raise ParticipationError("La participación ya no está activa.")
    if participation.need.end_at <= timezone.now():
        raise ParticipationError("La necesidad ya ha terminado.")
    return _end(participation, Participation.Status.REMOVED)