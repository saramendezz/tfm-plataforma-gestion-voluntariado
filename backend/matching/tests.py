import datetime as dt

import pytest
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from matching.models import PostalCode
from matching.services import evaluate, haversine_km, load_coordinates
from needs.models import Need
from profiles.models import AvailabilitySlot, OrganizationProfile, Skill, VolunteerProfile

PASSWORD = "Cl4ve-segura-2026"
HOUR = dt.timedelta(hours=1)
START = (timezone.now() + dt.timedelta(days=7)).replace(minute=0, second=0, microsecond=0)
END = START + 5 * HOUR
BCN = ("08001", 41.3797, 2.1682)
SBD = ("08201", 41.5463, 2.1086)
GIR = ("17001", 41.9794, 2.8214)


@pytest.fixture
def postal_codes(db):
    PostalCode.objects.bulk_create(
        [PostalCode(code=c, latitude=la, longitude=lo) for c, la, lo in (BCN, SBD, GIR)]
    )


@pytest.fixture
def first_aid(db):
    return Skill.objects.create(name="Primeros auxilios", category="health")


@pytest.fixture
def nursing(db):
    return Skill.objects.create(name="Enfermería", category="health")


def make_org(username="org", verified=True):
    user = User.objects.create_user(
        username, f"{username}@example.com", PASSWORD, role=User.Role.ORGANIZATION
    )
    return OrganizationProfile.objects.create(
        user=user,
        name=f"Entidad {username}",
        municipality="Barcelona",
        province="Barcelona",
        postal_code="08001",
        is_verified=verified,
    )


def make_need(org, postal="08001", skills=(), start=START, end=END, status=Need.Status.OPEN):
    need = Need.objects.create(
        organization=org,
        title="Necesidad",
        municipality="Barcelona",
        province="Barcelona",
        postal_code=postal,
        start_at=start,
        end_at=end,
        volunteers_needed=3,
        status=status,
    )
    need.required_skills.set(skills)
    return need


def make_volunteer(username, postal="08001", skills=(), slots=None, max_km=25, available=True):
    user = User.objects.create_user(
        username, f"{username}@example.com", PASSWORD, role=User.Role.VOLUNTEER
    )
    profile = VolunteerProfile.objects.create(
        user=user,
        municipality="Barcelona",
        province="Barcelona",
        postal_code=postal,
        phone="600000000",
        max_distance_km=max_km,
        is_available=available,
    )
    profile.skills.set(skills)
    for start, end in slots if slots is not None else [(START - HOUR, END + HOUR)]:
        AvailabilitySlot.objects.create(volunteer=profile, start_at=start, end_at=end)
    return profile


def run(profile, need):
    profile = VolunteerProfile.objects.prefetch_related(
        "skills", "availability_slots"
    ).get(pk=profile.pk)
    need = Need.objects.prefetch_related("required_skills").get(pk=need.pk)
    coordinates = load_coordinates([profile.postal_code, need.postal_code])
    return evaluate(profile, need, coordinates)


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def test_haversine_known_distance():
    assert 80 < haversine_km(*BCN[1:], *GIR[1:]) < 92


@pytest.mark.django_db
def test_full_match_scores_100(postal_codes, first_aid):
    need = make_need(make_org(), skills=[first_aid])
    result = run(make_volunteer("ana", skills=[first_aid]), need)
    assert result.score == pytest.approx(100)
    assert result.distance_km == 0


@pytest.mark.django_db
def test_unavailable_volunteer_is_excluded(postal_codes, first_aid):
    need = make_need(make_org(), skills=[first_aid])
    vol = make_volunteer("ana", skills=[first_aid], available=False)
    assert run(vol, need) is None


@pytest.mark.django_db
def test_partial_slot_coverage_is_excluded(postal_codes, first_aid):
    need = make_need(make_org(), skills=[first_aid])
    vol = make_volunteer("ana", skills=[first_aid], slots=[(START - HOUR, END - HOUR)])
    assert run(vol, need) is None


@pytest.mark.django_db
def test_contiguous_slots_cover_the_need(postal_codes, first_aid):
    need = make_need(make_org(), skills=[first_aid])
    middle = START + 2 * HOUR
    vol = make_volunteer(
        "ana",
        skills=[first_aid],
        slots=[(START - HOUR, middle), (middle, END + HOUR)],
    )
    assert run(vol, need) is not None


@pytest.mark.django_db
def test_gap_between_slots_does_not_cover(postal_codes, first_aid):
    need = make_need(make_org(), skills=[first_aid])
    vol = make_volunteer(
        "ana",
        skills=[first_aid],
        slots=[(START - HOUR, START + 2 * HOUR), (START + 3 * HOUR, END + HOUR)],
    )
    assert run(vol, need) is None


@pytest.mark.django_db
def test_partial_skills_lowers_score_and_lists_missing(postal_codes, first_aid, nursing):
    need = make_need(make_org(), skills=[first_aid, nursing])
    result = run(make_volunteer("ana", skills=[first_aid]), need)
    assert result.skills_score == 0.5
    assert result.skills_missing == ["Enfermería"]
    assert result.score < 100


@pytest.mark.django_db
def test_no_common_skill_is_excluded(postal_codes, first_aid, nursing):
    need = make_need(make_org(), skills=[first_aid])
    assert run(make_volunteer("ana", skills=[nursing]), need) is None


@pytest.mark.django_db
def test_need_without_skills_accepts_any_volunteer(postal_codes):
    need = make_need(make_org())
    result = run(make_volunteer("ana"), need)
    assert result is not None
    assert result.skills_score == 1


@pytest.mark.django_db
def test_distance_within_limit_scores_by_proximity(postal_codes, first_aid):
    need = make_need(make_org(), skills=[first_aid])
    vol = make_volunteer("ana", postal="08201", skills=[first_aid], max_km=25)
    result = run(vol, need)
    assert result is not None
    assert 15 < result.distance_km < 25
    assert result.distance_score == pytest.approx(1 - result.distance_km / 25)


@pytest.mark.django_db
def test_distance_beyond_limit_is_excluded(postal_codes, first_aid):
    need = make_need(make_org(), skills=[first_aid])
    near_limit = make_volunteer("ana", postal="17001", skills=[first_aid], max_km=25)
    wide_limit = make_volunteer("luis", postal="17001", skills=[first_aid], max_km=100)
    assert run(near_limit, need) is None
    assert run(wide_limit, need) is not None


@pytest.mark.django_db
def test_unknown_postal_code_is_excluded(postal_codes, first_aid):
    need = make_need(make_org(), skills=[first_aid])
    assert run(make_volunteer("ana", postal="99999", skills=[first_aid]), need) is None


@pytest.mark.django_db
def test_weights_are_configurable(postal_codes, first_aid, settings):
    need = make_need(make_org(), skills=[first_aid])
    vol = make_volunteer("ana", postal="08201", skills=[first_aid])
    default = run(vol, need)
    settings.MATCHING_WEIGHTS = {"skills": 1, "distance": 0}
    only_skills = run(vol, need)
    assert default.score < 100
    assert only_skills.score == pytest.approx(100)


@pytest.mark.django_db
def test_inactive_skills_are_ignored(postal_codes, first_aid, nursing):
    nursing.is_active = False
    nursing.save()
    need = make_need(make_org(), skills=[first_aid, nursing])
    result = run(make_volunteer("ana", skills=[first_aid]), need)
    assert result.skills_score == 1
    assert result.skills_missing == []


@pytest.mark.django_db
def test_candidates_are_ranked_and_filtered(postal_codes, first_aid, nursing):
    org = make_org()
    need = make_need(org, skills=[first_aid, nursing])
    make_volunteer("best", skills=[first_aid, nursing])
    make_volunteer("mid", postal="08201", skills=[first_aid])
    make_volunteer("noskills")
    make_volunteer("far", postal="17001", skills=[first_aid, nursing])
    make_volunteer("busy", skills=[first_aid], available=False)
    r = client_for(org.user).get(f"/api/needs/{need.id}/candidates/")
    assert r.status_code == 200
    assert [c["username"] for c in r.data] == ["best", "mid"]
    assert r.data[0]["score"] > r.data[1]["score"]
    assert r.data[1]["skills_missing"] == ["Enfermería"]
    assert not {"phone", "email"} & set(r.data[0])


@pytest.mark.django_db
def test_candidates_of_another_organization_is_404(postal_codes):
    need = make_need(make_org("org1"))
    other = make_org("org2")
    r = client_for(other.user).get(f"/api/needs/{need.id}/candidates/")
    assert r.status_code == 404


@pytest.mark.django_db
def test_candidates_forbidden_for_volunteer_and_unverified_org(postal_codes):
    need = make_need(make_org())
    volunteer = make_volunteer("ana")
    unverified = make_org("nover", verified=False)
    url = f"/api/needs/{need.id}/candidates/"
    assert client_for(volunteer.user).get(url).status_code == 403
    assert client_for(unverified.user).get(url).status_code == 403


@pytest.mark.django_db
def test_candidates_of_closed_need_is_400(postal_codes):
    org = make_org()
    need = make_need(org, status=Need.Status.CLOSED)
    r = client_for(org.user).get(f"/api/needs/{need.id}/candidates/")
    assert r.status_code == 400


@pytest.mark.django_db
def test_volunteer_sees_only_compatible_open_future_needs_ranked(
    postal_codes, first_aid, nursing
):
    org = make_org()
    near = make_need(org, skills=[first_aid])
    farther = make_need(org, postal="08201", skills=[first_aid])
    make_need(org, postal="17001", skills=[first_aid])
    make_need(org, skills=[nursing])
    make_need(org, skills=[first_aid], status=Need.Status.CLOSED)
    past_start, past_end = START - dt.timedelta(days=10), END - dt.timedelta(days=10)
    make_need(org, skills=[first_aid], start=past_start, end=past_end)
    make_need(make_org("nover", verified=False), skills=[first_aid])
    vol = make_volunteer(
        "ana",
        skills=[first_aid],
        slots=[(START - HOUR, END + HOUR), (past_start - HOUR, past_end + HOUR)],
    )
    r = client_for(vol.user).get("/api/needs/compatible/")
    assert r.status_code == 200
    assert [n["id"] for n in r.data] == [near.id, farther.id]
    assert r.data[0]["score"] > r.data[1]["score"]


@pytest.mark.django_db
def test_compatible_needs_forbidden_for_organization(postal_codes):
    org = make_org()
    assert client_for(org.user).get("/api/needs/compatible/").status_code == 403


@pytest.mark.django_db
def test_matching_endpoints_require_authentication():
    client = APIClient()
    assert client.get("/api/needs/compatible/").status_code == 401
    assert client.get("/api/needs/1/candidates/").status_code == 401


@pytest.mark.django_db
def test_load_postal_codes_averages_and_is_idempotent(tmp_path):
    file = tmp_path / "ES.txt"
    file.write_text(
        "ES\t08001\tA\tCat\tCT\tBarcelona\tB\t\t\t41.0\t2.0\t4\n"
        "ES\t08001\tB\tCat\tCT\tBarcelona\tB\t\t\t42.0\t3.0\t4\n"
        "ES\t17001\tGirona\tCat\tCT\tGirona\tGI\t\t\t41.98\t2.82\t6\n",
        encoding="utf-8",
    )
    call_command("load_postal_codes", str(file))
    call_command("load_postal_codes", str(file))
    assert PostalCode.objects.count() == 2
    barcelona = PostalCode.objects.get(code="08001")
    assert barcelona.latitude == pytest.approx(41.5)
    assert barcelona.longitude == pytest.approx(2.5)