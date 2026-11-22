from io import StringIO
from types import SimpleNamespace as NS

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from accounts.models import User
from matching.analysis import top_overlap
from matching.models import PostalCode
from needs.models import Need


@pytest.fixture
def demo_data(db):
    PostalCode.objects.bulk_create(
        [
            PostalCode(code=f"08{n:03d}", latitude=41.38 + n * 0.003, longitude=2.17 + n * 0.003)
            for n in range(1, 21)
        ]
    )
    call_command("seed_skills")


def test_top_overlap_counts_shared_top_candidates():
    def v(i):
        return NS(id=i)

    base = [(v(1), None), (v(2), None), (v(3), None), (v(4), None)]
    other = [(v(3), None), (v(1), None), (v(4), None), (v(2), None)]
    assert top_overlap(base, other, 3) == pytest.approx(2 / 3)
    assert top_overlap([], other) is None


@pytest.mark.django_db
def test_seed_demo_creates_data_and_can_be_reset(demo_data):
    call_command("seed_demo", "--volunteers", "12", "--reset")
    call_command("seed_demo", "--volunteers", "12", "--reset")
    assert User.objects.filter(username__startswith="demo_vol").count() == 12
    assert Need.objects.count() == 6


@pytest.mark.django_db
def test_seed_demo_refuses_to_duplicate_without_reset(demo_data):
    call_command("seed_demo", "--volunteers", "5", "--reset")
    with pytest.raises(CommandError):
        call_command("seed_demo", "--volunteers", "5")


@pytest.mark.django_db
def test_analyze_weights_report_and_csv(demo_data, tmp_path):
    call_command("seed_demo", "--volunteers", "30", "--reset")
    out = StringIO()
    path = tmp_path / "resultados.csv"
    call_command("analyze_weights", "--csv", str(path), stdout=out)
    assert "Necesidad:" in out.getvalue()
    assert path.read_text(encoding="utf-8").startswith("necesidad")