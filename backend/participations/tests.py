import pytest
from django.utils import timezone

from matching.tests import (  # noqa: F401
    END,
    HOUR,
    START,
    client_for,
    first_aid,
    make_need,
    make_org,
    make_volunteer,
    nursing,
    postal_codes,
)
from participations.models import Participation


def accept(volunteer, need):
    return client_for(volunteer.user).post(f"/api/needs/{need.id}/accept/")


def small_need(org, capacity=1, **kwargs):
    need = make_need(org, **kwargs)
    need.volunteers_needed = capacity
    need.save()
    return need


@pytest.mark.django_db
def test_volunteer_accepts_compatible_need(postal_codes, first_aid):
    need = make_need(make_org(), skills=[first_aid])
    vol = make_volunteer("ana", skills=[first_aid])
    r = accept(vol, need)
    assert r.status_code == 201
    assert r.data["status"] == "confirmed"
    assert Participation.objects.filter(volunteer=vol, need=need).count() == 1


@pytest.mark.django_db
def test_incompatible_need_cannot_be_accepted(postal_codes, first_aid):
    need = make_need(make_org(), skills=[first_aid])
    vol = make_volunteer("ana", skills=[])
    r = accept(vol, need)
    assert r.status_code == 400
    assert not Participation.objects.exists()


@pytest.mark.django_db
def test_capacity_is_enforced(postal_codes, first_aid):
    need = small_need(make_org(), skills=[first_aid])
    first = make_volunteer("ana", skills=[first_aid])
    second = make_volunteer("luis", skills=[first_aid])
    assert accept(first, need).status_code == 201
    r = accept(second, need)
    assert r.status_code == 400
    assert "todos los voluntarios" in r.data[0]


@pytest.mark.django_db
def test_overlapping_participation_is_rejected_but_adjacent_is_allowed(
    postal_codes, first_aid
):
    org = make_org()
    one = make_need(org, skills=[first_aid])
    overlapping = make_need(
        org, skills=[first_aid], start=START + HOUR, end=END + HOUR
    )
    adjacent = make_need(org, skills=[first_aid], start=END, end=END + HOUR)
    vol = make_volunteer(
        "ana", skills=[first_aid], slots=[(START - HOUR, END + 3 * HOUR)]
    )
    assert accept(vol, one).status_code == 201
    r = accept(vol, overlapping)
    assert r.status_code == 400
    assert "se solapa" in r.data[0]
    assert accept(vol, adjacent).status_code == 201


@pytest.mark.django_db
def test_cannot_accept_twice(postal_codes, first_aid):
    need = make_need(make_org(), skills=[first_aid])
    vol = make_volunteer("ana", skills=[first_aid])
    assert accept(vol, need).status_code == 201
    r = accept(vol, need)
    assert r.status_code == 400
    assert "Ya participas" in r.data[0]


@pytest.mark.django_db
def test_cannot_accept_closed_or_started_need(postal_codes, first_aid):
    org = make_org()
    closed = make_need(org, skills=[first_aid], status="closed")
    now = timezone.now()
    started = make_need(
        org, skills=[first_aid], start=now - HOUR, end=now + HOUR
    )
    vol = make_volunteer(
        "ana", skills=[first_aid], slots=[(now - 2 * HOUR, END + HOUR)]
    )
    assert "no está abierta" in accept(vol, closed).data[0]
    assert "ya ha comenzado" in accept(vol, started).data[0]


@pytest.mark.django_db
def test_withdraw_frees_the_spot(postal_codes, first_aid):
    need = small_need(make_org(), skills=[first_aid])
    first = make_volunteer("ana", skills=[first_aid])
    second = make_volunteer("luis", skills=[first_aid])
    participation_id = accept(first, need).data["id"]
    assert accept(second, need).status_code == 400
    r = client_for(first.user).post(f"/api/participations/{participation_id}/withdraw/")
    assert r.status_code == 200
    assert r.data["status"] == "withdrawn"
    assert accept(second, need).status_code == 201


@pytest.mark.django_db
def test_withdrawn_volunteer_can_accept_again(postal_codes, first_aid):
    need = make_need(make_org(), skills=[first_aid])
    vol = make_volunteer("ana", skills=[first_aid])
    participation_id = accept(vol, need).data["id"]
    client_for(vol.user).post(f"/api/participations/{participation_id}/withdraw/")
    assert accept(vol, need).status_code == 201
    assert Participation.objects.filter(volunteer=vol, need=need).count() == 2


@pytest.mark.django_db
def test_cannot_withdraw_after_start(postal_codes, first_aid):
    now = timezone.now()
    need = make_need(make_org(), skills=[first_aid], start=now - HOUR, end=now + HOUR)
    vol = make_volunteer("ana", skills=[first_aid])
    participation = Participation.objects.create(volunteer=vol, need=need)
    r = client_for(vol.user).post(f"/api/participations/{participation.id}/withdraw/")
    assert r.status_code == 400
    assert "ya ha comenzado" in r.data[0]


@pytest.mark.django_db
def test_organization_sees_participants_with_contact(postal_codes, first_aid):
    org = make_org("org1")
    need = make_need(org, skills=[first_aid])
    vol = make_volunteer("ana", skills=[first_aid])
    url = f"/api/needs/{need.id}/participants/"
    assert client_for(org.user).get(url).data == []
    accept(vol, need)
    r = client_for(org.user).get(url)
    assert r.status_code == 200
    assert len(r.data) == 1
    assert r.data[0]["username"] == "ana"
    assert r.data[0]["email"] == "ana@example.com"
    assert r.data[0]["phone"] == "600000000"
    assert client_for(make_org("org2").user).get(url).status_code == 404
    assert client_for(vol.user).get(url).status_code == 403


@pytest.mark.django_db
def test_organization_removes_volunteer_and_blocks_reaccept(postal_codes, first_aid):
    org = make_org("org1")
    need = make_need(org, skills=[first_aid])
    vol = make_volunteer("ana", skills=[first_aid])
    participation_id = accept(vol, need).data["id"]
    url = f"/api/participations/{participation_id}/remove/"
    assert client_for(make_org("org2").user).post(url).status_code == 404
    r = client_for(org.user).post(url)
    assert r.status_code == 200
    assert r.data["status"] == "removed"
    assert client_for(org.user).get(f"/api/needs/{need.id}/participants/").data == []
    again = accept(vol, need)
    assert again.status_code == 400
    assert "ha retirado" in again.data[0]


@pytest.mark.django_db
def test_cannot_withdraw_someone_elses_participation(postal_codes, first_aid):
    need = make_need(make_org(), skills=[first_aid])
    first = make_volunteer("ana", skills=[first_aid])
    second = make_volunteer("luis", skills=[first_aid])
    participation_id = accept(first, need).data["id"]
    r = client_for(second.user).post(f"/api/participations/{participation_id}/withdraw/")
    assert r.status_code == 404


@pytest.mark.django_db
def test_my_participations_lists_only_own(postal_codes, first_aid):
    org = make_org()
    first_need = make_need(org, skills=[first_aid])
    second_need = make_need(org, skills=[first_aid], start=END, end=END + HOUR)
    ana = make_volunteer(
        "ana", skills=[first_aid], slots=[(START - HOUR, END + 2 * HOUR)]
    )
    luis = make_volunteer("luis", skills=[first_aid])
    accept(ana, first_need)
    accept(ana, second_need)
    r = client_for(ana.user).get("/api/participations/")
    assert r.status_code == 200
    assert len(r.data) == 2
    assert {p["need"]["id"] for p in r.data} == {first_need.id, second_need.id}
    assert client_for(luis.user).get("/api/participations/").data == []


@pytest.mark.django_db
def test_need_of_unverified_organization_cannot_be_accepted(postal_codes, first_aid):
    need = make_need(make_org("nover", verified=False), skills=[first_aid])
    vol = make_volunteer("ana", skills=[first_aid])
    assert accept(vol, need).status_code == 404


@pytest.mark.django_db
def test_participation_permissions(postal_codes, first_aid):
    from rest_framework.test import APIClient

    org = make_org()
    need = make_need(org, skills=[first_aid])
    assert client_for(org.user).post(f"/api/needs/{need.id}/accept/").status_code == 403
    vol = make_volunteer("ana", skills=[first_aid])
    assert client_for(vol.user).get(f"/api/needs/{need.id}/participants/").status_code == 403
    anonymous = APIClient()
    assert anonymous.post(f"/api/needs/{need.id}/accept/").status_code == 401
    assert anonymous.get(f"/api/needs/{need.id}/participants/").status_code == 401