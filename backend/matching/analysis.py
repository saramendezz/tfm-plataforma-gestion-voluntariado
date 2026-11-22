from .services import evaluate


def rank_candidates(volunteers, need, coordinates, weights=None):
    """Lista de (voluntario, resultado) ordenada por puntuación y, a igualdad, por cercanía."""
    results = []
    for volunteer in volunteers:
        match = evaluate(volunteer, need, coordinates, weights)
        if match:
            results.append((volunteer, match))
    results.sort(key=lambda item: (-item[1].score, item[1].distance_km))
    return results


def top_ids(ranking, k=3):
    return [volunteer.id for volunteer, _ in ranking[:k]]


def top_overlap(base, other, k=3):
    """Proporción de los k primeros del ranking base que siguen entre los k primeros del otro."""
    base_top = top_ids(base, k)
    if not base_top:
        return None
    return len(set(base_top) & set(top_ids(other, k))) / len(base_top)