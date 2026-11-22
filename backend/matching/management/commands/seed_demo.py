import datetime as dt
import random

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from matching.models import PostalCode
from matching.services import haversine_km
from needs.models import Need
from profiles.models import AvailabilitySlot, OrganizationProfile, Skill, VolunteerProfile

PASSWORD = "Demo-2026-pass"

NEEDS = [
    ("Distribución de alimentos", ["Distribución de alimentos", "Carga y descarga"]),
    ("Atención sanitaria básica", ["Primeros auxilios", "Enfermería"]),
    ("Retirada de escombros", ["Carga y descarga", "Manejo de maquinaria"]),
    ("Apoyo a personas mayores", ["Atención a personas mayores", "Apoyo psicológico"]),
    ("Reparación del suministro eléctrico", ["Electricidad"]),
    ("Traducción en el centro de acogida", ["Inglés", "Francés", "Traducción"]),
]


def at(day, hour):
    return timezone.make_aware(dt.datetime.combine(day, dt.time(hour)))


class Command(BaseCommand):
    help = "Crea datos ficticios (voluntarios, organizaciones y necesidades) para demostración y evaluación."

    def add_arguments(self, parser):
        parser.add_argument("--volunteers", type=int, default=30)
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Elimina antes los datos de demostración existentes.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        rng = random.Random(options["seed"])

        if options["reset"]:
            User.objects.filter(username__startswith="demo_").delete()
        elif User.objects.filter(username__startswith="demo_").exists():
            raise CommandError("Ya hay datos de demostración. Usa --reset para recrearlos.")

        center = PostalCode.objects.filter(code="08001").first()
        if center is None:
            raise CommandError("Faltan los códigos postales. Ejecuta load_postal_codes.")
        nearby = sorted(
            PostalCode.objects.filter(code__startswith="08"),
            key=lambda p: haversine_km(center.latitude, center.longitude, p.latitude, p.longitude),
        )
        pool = [p.code for p in nearby[:60]]
        if len(pool) < 10:
            raise CommandError("Hay pocos códigos postales de la provincia de Barcelona.")

        skills = list(Skill.objects.filter(is_active=True))
        by_name = {s.name: s for s in skills}
        needed = {name for _, names in NEEDS for name in names}
        if needed - set(by_name):
            raise CommandError("Faltan habilidades del catálogo. Ejecuta seed_skills.")

        today = timezone.localdate()
        days = [today + dt.timedelta(days=d) for d in (2, 3, 4)]
        hashed = make_password(PASSWORD)

        orgs = []
        for n in (1, 2):
            user = User.objects.create(
                username=f"demo_org{n}",
                email=f"demo_org{n}@example.com",
                password=hashed,
                role=User.Role.ORGANIZATION,
            )
            orgs.append(
                OrganizationProfile.objects.create(
                    user=user,
                    name=f"Asociación de ejemplo {n}",
                    municipality="Barcelona",
                    province="Barcelona",
                    postal_code="08001",
                    is_verified=True,
                )
            )

        for i, (title, skill_names) in enumerate(NEEDS):
            day = days[i % 3]
            start_hour, end_hour = (9, 14) if i % 2 == 0 else (15, 20)
            need = Need.objects.create(
                organization=orgs[i % 2],
                title=title,
                description="Necesidad de demostración",
                municipality="Barcelona",
                province="Barcelona",
                postal_code=rng.choice(pool),
                start_at=at(day, start_hour),
                end_at=at(day, end_hour),
                volunteers_needed=rng.randint(2, 5),
            )
            need.required_skills.set([by_name[name] for name in skill_names])

        for n in range(1, options["volunteers"] + 1):
            user = User.objects.create(
                username=f"demo_vol{n:02d}",
                email=f"demo_vol{n:02d}@example.com",
                password=hashed,
                role=User.Role.VOLUNTEER,
            )
            profile = VolunteerProfile.objects.create(
                user=user,
                municipality="Barcelona",
                province="Barcelona",
                postal_code=rng.choice(pool),
                max_distance_km=rng.choice([10, 25, 25, 50, 100]),
                is_available=rng.random() < 0.9,
            )
            profile.skills.set(rng.sample(skills, rng.randint(2, 5)))
            for day in days:
                if rng.random() < 0.7:
                    AvailabilitySlot.objects.create(
                        volunteer=profile, start_at=at(day, 8), end_at=at(day, 21)
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Creadas {len(orgs)} organizaciones, {len(NEEDS)} necesidades y "
                f"{options['volunteers']} voluntarios (semilla {options['seed']})."
            )
        )
        self.stdout.write(f"Usuarios: demo_org1, demo_org2, demo_vol01... Contraseña: {PASSWORD}")