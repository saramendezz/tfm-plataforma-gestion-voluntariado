from django.core.management.base import BaseCommand

from profiles.models import Skill

SKILLS = {
    "health": [
        "Primeros auxilios",
        "Soporte vital básico (RCP)",
        "Enfermería",
        "Medicina",
    ],
    "logistics": [
        "Conducción de vehículos",
        "Conducción de vehículos todoterreno",
        "Carga y descarga",
        "Gestión de almacén",
        "Distribución de alimentos",
    ],
    "technical": [
        "Electricidad",
        "Fontanería",
        "Albañilería",
        "Mecánica",
        "Manejo de maquinaria",
    ],
    "communication": [
        "Inglés",
        "Francés",
        "Lengua de signos",
        "Traducción",
        "Comunicación en redes sociales",
    ],
    "social": [
        "Apoyo psicológico",
        "Atención a personas mayores",
        "Cuidado de menores",
        "Acompañamiento a personas dependientes",
    ],
    "coordination": [
        "Coordinación de equipos",
        "Gestión de voluntariado",
        "Apoyo administrativo y registro de datos",
    ],
}


class Command(BaseCommand):
    help = "Carga el catálogo inicial de habilidades (se puede ejecutar varias veces)."

    def handle(self, *args, **options):
        created = 0
        for category, names in SKILLS.items():
            for name in names:
                _, was_created = Skill.objects.get_or_create(
                    name=name, defaults={"category": category}
                )
                created += was_created
        self.stdout.write(self.style.SUCCESS(f"Habilidades nuevas: {created}"))