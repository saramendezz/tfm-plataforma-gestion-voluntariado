import pytest
from django.core.management import call_command

from profiles.models import Skill


@pytest.mark.django_db
def test_seed_skills_is_idempotent():
    call_command("seed_skills")
    total = Skill.objects.count()
    call_command("seed_skills")
    assert Skill.objects.count() == total > 0