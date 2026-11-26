import pytest
from rest_framework.test import APIClient

from accounts.models import User
from needs.models import Need
from profiles.models import OrganizationProfile, Skill, VolunteerProfile
from participations.models import Participation

PASSWORD = "Cl4ve-segura-2026"


def make_org(username, verified=True):
    user = User.objects.create_user(
        username, f"{username}@example.com", PASSWORD, role=User.Role.ORGANIZATION
    )
    profile = OrganizationProfile.objects.create(
        user=user,
        name=f"Entidad {username}",
        municipality="Barcelona",
        province="Barcelona",
        postal_code="08001",
        is_verified=verified,
    )
    client = APIClient()
    client.force_authenticate(user)
    return profile, client


def payload(**extra):
    return {
        "title": "Limpieza de calles",
        "description": "Retirada de barro y escombros",
        "municipality": "Barcelona",
        "province": "Barcelona",
        "postal_code": "08001",
        "start_at": "2026-11-20T09:00:00+01:00",
        "end_at": "2026-11-20T14:00:00+01:00",
        "volunteers_needed": 5,
        **extra,
    }


@pytest.mark.django_db
def test_verified_org_creates_need():
    profile, client = make_org("org1")
    r = client.post("/api/needs/", payload(), format="json")
    assert r.status_code == 201
    assert r.data["status"] == "open"
    assert Need.objects.get(pk=r.data["id"]).organization == profile


@pytest.mark.django_db
def test_need_with_required_skills():
    _, client = make_org("org1")
    skill = Skill.objects.create(name="Primeros auxilios", category="health")
    r = client.post(
        "/api/needs/", payload(required_skills=[skill.id]), format="json"
    )
    assert r.status_code == 201
    assert r.data["required_skills"] == [skill.id]


@pytest.mark.django_db
def test_inactive_skill_is_rejected():
    _, client = make_org("org1")
    inactive = Skill.objects.create(name="Antigua", category="health", is_active=False)
    r = client.post(
        "/api/needs/", payload(required_skills=[inactive.id]), format="json"
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_unverified_org_cannot_create():
    _, client = make_org("org1", verified=False)
    r = client.post("/api/needs/", payload(), format="json")
    assert r.status_code == 403
    assert Need.objects.count() == 0


@pytest.mark.django_db
def test_volunteer_cannot_access_needs():
    user = User.objects.create_user(
        "ana", "ana@example.com", PASSWORD, role=User.Role.VOLUNTEER
    )
    client = APIClient()
    client.force_authenticate(user)
    assert client.get("/api/needs/").status_code == 403


@pytest.mark.django_db
def test_end_must_be_after_start():
    _, client = make_org("org1")
    r = client.post(
        "/api/needs/",
        payload(end_at="2026-11-20T08:00:00+01:00"),
        format="json",
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_organization_only_sees_its_own_needs():
    _, client1 = make_org("org1")
    _, client2 = make_org("org2")
    created = client1.post("/api/needs/", payload(), format="json").data
    assert [n["id"] for n in client1.get("/api/needs/").data] == [created["id"]]
    assert client2.get("/api/needs/").data == []
    assert client2.get(f"/api/needs/{created['id']}/").status_code == 404
    r = client2.patch(f"/api/needs/{created['id']}/", {"title": "x"}, format="json")
    assert r.status_code == 404


@pytest.mark.django_db
def test_update_and_close_need():
    _, client = make_org("org1")
    need_id = client.post("/api/needs/", payload(), format="json").data["id"]
    r = client.patch(f"/api/needs/{need_id}/", {"title": "Nuevo título"}, format="json")
    assert r.status_code == 200
    assert r.data["title"] == "Nuevo título"
    closed = client.post(f"/api/needs/{need_id}/close/")
    assert closed.status_code == 200
    assert closed.data["status"] == "closed"
    r = client.patch(f"/api/needs/{need_id}/", {"title": "Otro"}, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_filter_by_status():
    _, client = make_org("org1")
    first = client.post("/api/needs/", payload(), format="json").data["id"]
    client.post("/api/needs/", payload(title="Segunda"), format="json")
    client.post(f"/api/needs/{first}/close/")
    assert len(client.get("/api/needs/?status=closed").data) == 1
    assert len(client.get("/api/needs/?status=open").data) == 1
    assert len(client.get("/api/needs/").data) == 2


@pytest.mark.django_db
def test_endpoints_require_authentication():
    client = APIClient()
    assert client.get("/api/needs/").status_code == 401

@pytest.mark.django_db
def test_need_with_participants_cannot_change_schedule_or_shrink():
    _, client = make_org("org1")
    need_id = client.post("/api/needs/", payload(), format="json").data["id"]
    for name in ("ana", "luis"):
        user = User.objects.create_user(
            name, f"{name}@example.com", PASSWORD, role=User.Role.VOLUNTEER
        )
        volunteer = VolunteerProfile.objects.create(user=user)
        Participation.objects.create(volunteer=volunteer, need_id=need_id)
    url = f"/api/needs/{need_id}/"

    r = client.patch(url, {"start_at": "2026-11-20T10:00:00+01:00"}, format="json")
    assert r.status_code == 400
    assert client.patch(url, {"volunteers_needed": 1}, format="json").status_code == 400
    assert client.patch(url, {"volunteers_needed": 2}, format="json").status_code == 200
    r = client.patch(url, {"title": "Nuevo título"}, format="json")
    assert r.status_code == 200
    assert r.data["confirmed_count"] == 2