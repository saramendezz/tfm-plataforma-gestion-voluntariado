from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

postal_code_validator = RegexValidator(
    r"^\d{5}$", "El código postal debe tener 5 dígitos."
)


class Skill(models.Model):
    """Catálogo cerrado de habilidades, gestionado por el administrador."""

    class Category(models.TextChoices):
        HEALTH = "health", "Sanitaria"
        LOGISTICS = "logistics", "Logística y transporte"
        TECHNICAL = "technical", "Técnica y oficios"
        COMMUNICATION = "communication", "Comunicación e idiomas"
        SOCIAL = "social", "Atención y acompañamiento"
        COORDINATION = "coordination", "Coordinación"

    name = models.CharField(max_length=80, unique=True)
    category = models.CharField(max_length=20, choices=Category.choices)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return self.name


class Location(models.Model):
    municipality = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=5, validators=[postal_code_validator])

    class Meta:
        abstract = True


class VolunteerProfile(Location):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="volunteer_profile",
    )
    phone = models.CharField(max_length=20, blank=True)
    skills = models.ManyToManyField(
        Skill,
        blank=True,
        related_name="volunteers",
        limit_choices_to={"is_active": True},
    )
    max_distance_km = models.PositiveSmallIntegerField(
        default=25,
        validators=[MinValueValidator(1), MaxValueValidator(500)],
    )
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Voluntario: {self.user.username}"


class OrganizationProfile(Location):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_profile",
    )
    name = models.CharField(max_length=150)
    description = models.CharField(max_length=500, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name