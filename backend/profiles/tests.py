import pytest
from django.core.exceptions import ValidationError

from accounts.models import User
from profiles.models import Skill, VolunteerProfile


@pytest.fixture
def volunteer_user():
    return User.objects.create_user(
        "ana", "ana@example.com", "clave12345", role=User.Role.VOLUNTEER
    )


@pytest.mark.django_db
def test_volunteer_profile_with_skills(volunteer_user):
    skill = Skill.objects.create(
        name="Primeros auxilios", category=Skill.Category.HEALTH
    )
    profile = VolunteerProfile.objects.create(
        user=volunteer_user,
        municipality="Barcelona",
        province="Barcelona",
        postal_code="08001",
    )
    profile.skills.add(skill)
    assert profile.skills.count() == 1


@pytest.mark.django_db
def test_invalid_postal_code_is_rejected(volunteer_user):
    profile = VolunteerProfile(
        user=volunteer_user,
        municipality="Barcelona",
        province="Barcelona",
        postal_code="123",
    )
    with pytest.raises(ValidationError):
        profile.full_clean()