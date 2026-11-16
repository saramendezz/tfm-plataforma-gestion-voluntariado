import pytest
from rest_framework.test import APIClient

from accounts.models import User
from profiles.models import AvailabilitySlot, VolunteerProfile

PASSWORD = "Cl4ve-segura-2026"


def make_volunteer(username):
    user = User.objects.create_user(
        username, f"{username}@example.com", PASSWORD, role=User.Role.VOLUNTEER
    )
    VolunteerProfile.objects.create(user=user)
    client = APIClient()
    client.force_authenticate(user)
    return user, client


def slot(start="2026-11-20T09:00:00+01:00", end="2026-11-20T14:00:00+01:00"):
    return {"start_at": start, "end_at": end}


@pytest.mark.django_db
def test_volunteer_creates_and_lists_slots_in_order():
    _, client = make_volunteer("ana")
    later = slot("2026-11-21T09:00:00+01:00", "2026-11-21T14:00:00+01:00")
    assert client.post("/api/availability/", later, format="json").status_code == 201
    assert client.post("/api/availability/", slot(), format="json").status_code == 201
    r = client.get("/api/availability/")
    assert r.status_code == 200
    assert len(r.data) == 2
    assert r.data[0]["start_at"] < r.data[1]["start_at"]


@pytest.mark.django_db
def test_end_must_be_after_start():
    _, client = make_volunteer("ana")
    r = client.post(
        "/api/availability/",
        slot(end="2026-11-20T08:00:00+01:00"),
        format="json",
    )
    assert r.status_code == 400


@pytest.mark.django_db
def test_overlapping_slot_is_rejected_but_adjacent_is_allowed():
    _, client = make_volunteer("ana")
    client.post("/api/availability/", slot(), format="json")
    overlap = slot("2026-11-20T12:00:00+01:00", "2026-11-20T16:00:00+01:00")
    assert client.post("/api/availability/", overlap, format="json").status_code == 400
    adjacent = slot("2026-11-20T14:00:00+01:00", "2026-11-20T18:00:00+01:00")
    assert client.post("/api/availability/", adjacent, format="json").status_code == 201


@pytest.mark.django_db
def test_volunteer_only_sees_own_slots():
    _, client1 = make_volunteer("ana")
    _, client2 = make_volunteer("luis")
    client1.post("/api/availability/", slot(), format="json")
    assert client2.get("/api/availability/").data == []


@pytest.mark.django_db
def test_delete_own_slot_but_not_someone_elses():
    _, client1 = make_volunteer("ana")
    _, client2 = make_volunteer("luis")
    slot_id = client1.post("/api/availability/", slot(), format="json").data["id"]
    assert client2.delete(f"/api/availability/{slot_id}/").status_code == 404
    assert client1.delete(f"/api/availability/{slot_id}/").status_code == 204
    assert AvailabilitySlot.objects.count() == 0


@pytest.mark.django_db
def test_organization_cannot_access_availability():
    user = User.objects.create_user(
        "org", "org@example.com", PASSWORD, role=User.Role.ORGANIZATION
    )
    client = APIClient()
    client.force_authenticate(user)
    assert client.get("/api/availability/").status_code == 403


@pytest.mark.django_db
def test_availability_requires_authentication():
    assert APIClient().get("/api/availability/").status_code == 401