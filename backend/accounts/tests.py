import pytest
from rest_framework.test import APIClient

from accounts.models import User
from profiles.models import OrganizationProfile, VolunteerProfile

PASSWORD = "Cl4ve-segura-2026"


@pytest.fixture
def client():
    return APIClient()


def payload(**extra):
    return {
        "username": "ana",
        "email": "ana@example.com",
        "password": PASSWORD,
        "role": "volunteer",
        **extra,
    }


@pytest.mark.django_db
def test_register_volunteer_creates_profile(client):
    r = client.post("/api/auth/register/", payload(), format="json")
    assert r.status_code == 201
    assert "password" not in r.data
    assert VolunteerProfile.objects.filter(user__username="ana").exists()


@pytest.mark.django_db
def test_register_organization_creates_profile(client):
    r = client.post(
        "/api/auth/register/", payload(role="organization"), format="json"
    )
    assert r.status_code == 201
    assert OrganizationProfile.objects.filter(user__username="ana").exists()


@pytest.mark.django_db
def test_cannot_register_as_admin(client):
    r = client.post("/api/auth/register/", payload(role="admin"), format="json")
    assert r.status_code == 400
    assert not User.objects.filter(username="ana").exists()


@pytest.mark.django_db
def test_duplicate_email_is_rejected(client):
    client.post("/api/auth/register/", payload(), format="json")
    r = client.post(
        "/api/auth/register/",
        payload(username="otra", email="ANA@example.com"),
        format="json",
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_weak_password_is_rejected(client):
    r = client.post("/api/auth/register/", payload(password="1234"), format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_login_and_me(client):
    client.post("/api/auth/register/", payload(), format="json")
    r = client.post(
        "/api/auth/login/", {"username": "ana", "password": PASSWORD}, format="json"
    )
    assert r.status_code == 200
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
    me = client.get("/api/auth/me/")
    assert me.status_code == 200
    assert me.data["role"] == "volunteer"


@pytest.mark.django_db
def test_me_requires_authentication(client):
    assert client.get("/api/auth/me/").status_code == 401