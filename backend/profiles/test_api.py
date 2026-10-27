import pytest
from rest_framework.test import APIClient

from accounts.models import User
from profiles.models import OrganizationProfile, Skill

PASSWORD = "Cl4ve-segura-2026"


@pytest.fixture
def make_client():
    def _make(username, role):
        user = User.objects.create_user(
            username, f"{username}@example.com", PASSWORD, role=role
        )
        client = APIClient()
        client.force_authenticate(user)
        return user, client

    return _make


@pytest.fixture
def skill():
    return Skill.objects.create(name="Primeros auxilios", category="health")


@pytest.mark.django_db
def test_volunteer_updates_own_profile(make_client, skill):
    _, client = make_client("ana", User.Role.VOLUNTEER)
    r = client.patch(
        "/api/profiles/volunteer/me/",
        {
            "municipality": "Barcelona",
            "province": "Barcelona",
            "postal_code": "08001",
            "skills": [skill.id],
        },
        format="json",
    )
    assert r.status_code == 200
    assert r.data["skills"] == [skill.id]
    assert client.get("/api/profiles/volunteer/me/").data["municipality"] == "Barcelona"


@pytest.mark.django_db
def test_invalid_postal_code_is_rejected(make_client):
    _, client = make_client("ana", User.Role.VOLUNTEER)
    r = client.patch(
        "/api/profiles/volunteer/me/", {"postal_code": "123"}, format="json"
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_inactive_skill_cannot_be_assigned(make_client):
    _, client = make_client("ana", User.Role.VOLUNTEER)
    inactive = Skill.objects.create(name="Antigua", category="health", is_active=False)
    r = client.patch(
        "/api/profiles/volunteer/me/", {"skills": [inactive.id]}, format="json"
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_volunteer_cannot_access_organization_profile(make_client):
    _, client = make_client("ana", User.Role.VOLUNTEER)
    assert client.get("/api/profiles/organization/me/").status_code == 403


@pytest.mark.django_db
def test_organization_cannot_access_volunteer_profile(make_client):
    _, client = make_client("luis", User.Role.ORGANIZATION)
    assert client.get("/api/profiles/volunteer/me/").status_code == 403


@pytest.mark.django_db
def test_organization_cannot_verify_itself(make_client):
    user, client = make_client("luis", User.Role.ORGANIZATION)
    r = client.patch(
        "/api/profiles/organization/me/",
        {"name": "Cruz Local", "is_verified": True},
        format="json",
    )
    assert r.status_code == 200
    assert OrganizationProfile.objects.get(user=user).is_verified is False


@pytest.mark.django_db
def test_skills_list_only_shows_active_ones(make_client, skill):
    Skill.objects.create(name="Antigua", category="health", is_active=False)
    _, client = make_client("ana", User.Role.VOLUNTEER)
    r = client.get("/api/skills/")
    assert r.status_code == 200
    assert [s["name"] for s in r.data] == ["Primeros auxilios"]


@pytest.mark.django_db
def test_endpoints_require_authentication():
    client = APIClient()
    assert client.get("/api/skills/").status_code == 401
    assert client.get("/api/profiles/volunteer/me/").status_code == 401