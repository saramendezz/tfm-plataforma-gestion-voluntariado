from django.core.validators import MinValueValidator
from django.db import models

from profiles.models import Location, OrganizationProfile, Skill


class Need(Location):
    class Status(models.TextChoices):
        OPEN = "open", "Abierta"
        CLOSED = "closed", "Cerrada"

    organization = models.ForeignKey(
        OrganizationProfile, on_delete=models.CASCADE, related_name="needs"
    )
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=500, blank=True)
    required_skills = models.ManyToManyField(
        Skill,
        blank=True,
        related_name="needs",
        limit_choices_to={"is_active": True},
    )
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    volunteers_needed = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1)]
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.OPEN
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title