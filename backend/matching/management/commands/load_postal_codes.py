from collections import defaultdict
import csv
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from matching.models import PostalCode


class Command(BaseCommand):
    help = "Carga las coordenadas de los códigos postales desde el fichero ES.txt de GeoNames."

    def add_arguments(self, parser):
        parser.add_argument(
            "path",
            nargs="?",
            default=str(Path(settings.BASE_DIR) / "data" / "ES.txt"),
        )

    def handle(self, *args, **options):
        path = Path(options["path"])
        if not path.exists():
            raise CommandError(f"No se encuentra el fichero: {path}")

        sums = defaultdict(lambda: [0.0, 0.0, 0])
        with path.open(encoding="utf-8", newline="") as file:
            for row in csv.reader(file, delimiter="\t", quoting=csv.QUOTE_NONE):
                if len(row) < 11:
                    continue
                try:
                    lat, lon = float(row[9]), float(row[10])
                except ValueError:
                    continue
                acc = sums[row[1].strip().zfill(5)]
                acc[0] += lat
                acc[1] += lon
                acc[2] += 1

        with transaction.atomic():
            PostalCode.objects.all().delete()
            PostalCode.objects.bulk_create(
                [
                    PostalCode(code=code, latitude=s[0] / s[2], longitude=s[1] / s[2])
                    for code, s in sums.items()
                ],
                batch_size=500,
            )
        self.stdout.write(self.style.SUCCESS(f"Códigos postales cargados: {len(sums)}"))