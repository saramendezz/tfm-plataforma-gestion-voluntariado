import csv

from django.core.management.base import BaseCommand
from django.utils import timezone

from matching.analysis import rank_candidates, top_overlap
from matching.services import get_weights, load_coordinates
from needs.models import Need
from profiles.models import VolunteerProfile

SKILL_WEIGHTS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]


class Command(BaseCommand):
    help = "Analiza cómo cambia el ranking de candidatos al variar los pesos de la compatibilidad."

    def add_arguments(self, parser):
        parser.add_argument("--csv", help="Ruta del CSV donde guardar los resultados.")
        parser.add_argument("--top", type=int, default=3)

    def handle(self, *args, **options):
        k = options["top"]
        needs = list(
            Need.objects.filter(
                status=Need.Status.OPEN,
                organization__is_verified=True,
                end_at__gt=timezone.now(),
            )
            .prefetch_related("required_skills")
            .order_by("id")
        )
        if not needs:
            self.stdout.write("No hay necesidades abiertas.")
            return

        volunteers = list(
            VolunteerProfile.objects.filter(is_available=True)
            .select_related("user")
            .prefetch_related("skills", "availability_slots")
        )
        coordinates = load_coordinates(
            {v.postal_code for v in volunteers} | {n.postal_code for n in needs}
        )
        w_base = get_weights()
        self.stdout.write(
            f"Voluntarios disponibles: {len(volunteers)}. Pesos base: "
            f"habilidades {w_base[0]:.1f} / distancia {w_base[1]:.1f}. Se compara el top-{k}."
        )

        rows = []
        overlaps = {w: [] for w in SKILL_WEIGHTS}
        covered = 0
        for need in needs:
            base = rank_candidates(volunteers, need, coordinates)
            enough = len(base) >= need.volunteers_needed
            covered += enough
            self.stdout.write(
                f"\nNecesidad: {need.title} (necesarios: {need.volunteers_needed}; "
                f"candidatos: {len(base)})"
            )
            if not base:
                continue
            for w_skills in SKILL_WEIGHTS:
                weights = {"skills": w_skills, "distance": round(1 - w_skills, 2)}
                ranking = rank_candidates(volunteers, need, coordinates, weights)
                overlap = top_overlap(base, ranking, k)
                overlaps[w_skills].append(overlap)
                top = ", ".join(v.user.username for v, _ in ranking[:k])
                self.stdout.write(
                    f"  habilidades {w_skills:.1f} / distancia {1 - w_skills:.1f}: "
                    f"{top}  (coincidencia con la base: {overlap:.0%})"
                )
                rows.append(
                    [need.title, w_skills, weights["distance"], len(base), top, round(overlap, 2)]
                )

        self.stdout.write(
            f"\nNecesidades con candidatos suficientes: {covered} de {len(needs)}."
        )
        self.stdout.write(f"Coincidencia media del top-{k} con los pesos base:")
        for w_skills in SKILL_WEIGHTS:
            values = [x for x in overlaps[w_skills] if x is not None]
            if values:
                mean = sum(values) / len(values)
                self.stdout.write(
                    f"  habilidades {w_skills:.1f} / distancia {1 - w_skills:.1f}: {mean:.0%}"
                )

        if options["csv"]:
            with open(options["csv"], "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(
                    ["necesidad", "peso_habilidades", "peso_distancia", "candidatos", "top", "coincidencia"]
                )
                writer.writerows(rows)
            self.stdout.write(f"Resultados guardados en {options['csv']}")