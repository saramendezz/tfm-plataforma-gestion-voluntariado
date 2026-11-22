from dataclasses import dataclass, field
from math import asin, cos, radians, sin, sqrt

from django.conf import settings

from .models import PostalCode

EARTH_RADIUS_KM = 6371.0088
DEFAULT_WEIGHTS = {"skills": 0.6, "distance": 0.4}


def haversine_km(lat1, lon1, lat2, lon2):
    phi1, phi2 = radians(lat1), radians(lat2)
    d_phi = phi2 - phi1
    d_lambda = radians(lon2 - lon1)
    a = sin(d_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def normalize_weights(weights):
    total = weights["skills"] + weights["distance"]
    return weights["skills"] / total, weights["distance"] / total


def get_weights():
    return normalize_weights(getattr(settings, "MATCHING_WEIGHTS", DEFAULT_WEIGHTS))

def load_coordinates(codes):
    codes = {code for code in codes if code}
    return {
        p.code: (p.latitude, p.longitude)
        for p in PostalCode.objects.filter(code__in=codes)
    }


def covers(slots, start, end):
    """Indica si las franjas, unidas si son contiguas, cubren todo [start, end]."""
    merged = []
    for slot_start, slot_end in sorted(slots):
        if merged and slot_start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], slot_end)
        else:
            merged.append([slot_start, slot_end])
    return any(s <= start and end <= e for s, e in merged)


@dataclass
class MatchResult:
    score: float
    skills_score: float
    distance_score: float
    distance_km: float
    skills_matched: list = field(default_factory=list)
    skills_missing: list = field(default_factory=list)

    def as_dict(self):
        return {
            "score": round(self.score, 1),
            "skills_score": round(self.skills_score, 2),
            "distance_score": round(self.distance_score, 2),
            "distance_km": round(self.distance_km, 1),
            "skills_matched": self.skills_matched,
            "skills_missing": self.skills_missing,
        }


def evaluate(volunteer, need, coordinates, weights=None):
    """Devuelve el resultado de compatibilidad o None si no es candidato.

    Se asume que las relaciones del voluntario (habilidades y franjas) y de la
    necesidad (habilidades requeridas) vienen precargadas.
    """
    # Filtro 1: disponibilidad general
    if not volunteer.is_available:
        return None

    # Filtro 2: las franjas cubren todo el intervalo de la necesidad
    slots = [(s.start_at, s.end_at) for s in volunteer.availability_slots.all()]
    if not covers(slots, need.start_at, need.end_at):
        return None

    # Filtro 3: al menos una de las habilidades requeridas (si las hay)
    required = {s.id: s.name for s in need.required_skills.all() if s.is_active}
    owned = {s.id for s in volunteer.skills.all() if s.is_active}
    matched = [name for sid, name in required.items() if sid in owned]
    missing = [name for sid, name in required.items() if sid not in owned]
    if required and not matched:
        return None

    # Filtro 4: la distancia no supera la máxima del voluntario
    origin = coordinates.get(volunteer.postal_code)
    target = coordinates.get(need.postal_code)
    if origin is None or target is None:
        return None
    distance = haversine_km(*origin, *target)
    max_distance = max(volunteer.max_distance_km, 1)
    if distance > max_distance:
        return None

    skills_score = len(matched) / len(required) if required else 1.0
    distance_score = 1 - distance / max_distance
    w_skills, w_distance = normalize_weights(weights) if weights else get_weights()
    score = 100 * (w_skills * skills_score + w_distance * distance_score)
    return MatchResult(
        score=score,
        skills_score=skills_score,
        distance_score=distance_score,
        distance_km=distance,
        skills_matched=matched,
        skills_missing=missing,
    )