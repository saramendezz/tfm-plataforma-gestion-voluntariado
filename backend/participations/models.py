from django.db import models
from django.db.models import Q

from needs.models import Need
from profiles.models import VolunteerProfile


class Participation(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmada"
        WITHDRAWN = "withdrawn", "Retirada por el voluntario"
        REMOVED = "removed", "Retirada por la organización"

    volunteer = models.ForeignKey(
        VolunteerProfile, on_delete=models.CASCADE, related_name="participations"
    )
    need = models.ForeignKey(
        Need, on_delete=models.CASCADE, related_name="participations"
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.CONFIRMED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["volunteer", "need"],
                condition=Q(status="confirmed"),
                name="unique_confirmed_participation",
            )
        ]

    def __str__(self):
        return f"{self.volunteer} → {self.need} ({self.status})"