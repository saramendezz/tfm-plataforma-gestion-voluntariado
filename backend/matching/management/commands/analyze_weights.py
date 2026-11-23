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
        overlaps = {w: [] for w in SKILL_WEIGHTS}  # necesidades con más de k candidatos
        firsts = {w: [] for w in SKILL_WEIGHTS}  # necesidades con 2 o más candidatos
        covered = 0
        for need in needs:
            base = rank_candidates(volunteers, need, coordinates)
            covered += len(base) >= need.volunteers_needed
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
                same_first = ranking[0][0].id == base[0][0].id
                if len(base) > k:
                    overlaps[w_skills].append(overlap)
                if len(base) >= 2:
                    firsts[w_skills].append(same_first)
                top = ", ".join(v.user.username for v, _ in ranking[:k])
                self.stdout.write(
                    f"  habilidades {w_skills:.1f} / distancia {1 - w_skills:.1f}: {top}  "
                    f"(top-{k}: {overlap:.0%}; mismo primero: {'sí' if same_first else 'no'})"
                )
                rows.append(
                    [
                        need.title,
                        w_skills,
                        weights["distance"],
                        len(base),
                        top,
                        round(overlap, 2),
                        int(same_first),
                    ]
                )

        self.stdout.write(
            f"\nNecesidades con candidatos suficientes: {covered} de {len(needs)}."
        )
        self.stdout.write(
            f"Coincidencia media del top-{k} (solo necesidades con más de {k} candidatos) "
            "y coincidencia del primer candidato (necesidades con 2 o más):"
        )
        for w_skills in SKILL_WEIGHTS:
            ov, fi = overlaps[w_skills], firsts[w_skills]
            ov_text = f"{sum(ov) / len(ov):.0%}" if ov else "—"
            fi_text = f"{sum(fi)} de {len(fi)}" if fi else "—"
            self.stdout.write(
                f"  habilidades {w_skills:.1f} / distancia {1 - w_skills:.1f}: "
                f"top-{k} {ov_text}; mismo primero {fi_text}"
            )

        if options["csv"]:
            with open(options["csv"], "w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(
                    [
                        "necesidad",
                        "peso_habilidades",
                        "peso_distancia",
                        "candidatos",
                        "top",
                        "coincidencia_top",
                        "mismo_primero",
                    ]
                )
                writer.writerows(rows)
            self.stdout.write(f"Resultados guardados en {options['csv']}")