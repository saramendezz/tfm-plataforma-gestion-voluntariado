import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";
import { formatDateTime } from "../dates";

export default function CompatibleNeeds() {
  const [needs, setNeeds] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    api
      .get("/needs/compatible/")
      .then((r) => {
        if (!cancelled) setNeeds(r.data);
      })
      .catch((err) => {
        if (cancelled) return;
        setNeeds([]);
        setError(errorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <>
      <h1>Necesidades para mí</h1>
      <p className="hint">
        Necesidades abiertas que encajan con tu disponibilidad, tus habilidades y tu distancia
        máxima de desplazamiento, ordenadas de mayor a menor compatibilidad.
      </p>

      {error && <p className="error">{error}</p>}
      {needs === null && <p>Cargando...</p>}
      {needs && needs.length === 0 && !error && (
        <p>
          Ahora mismo no hay necesidades compatibles. Comprueba que tu perfil tiene código postal
          y habilidades, que has indicado tu disponibilidad y que tu distancia máxima es suficiente.
        </p>
      )}

      {needs?.map((n) => (
        <article key={n.id} className="card">
          <h2>
            {n.title} <span className="score">{n.score}</span>
          </h2>
          <p>
            {n.organization_name} · {n.municipality} ({n.province}) · a {n.distance_km} km
          </p>
          <p>
            {formatDateTime(n.start_at)} → {formatDateTime(n.end_at)} · Voluntarios necesarios:{" "}
            {n.volunteers_needed}
          </p>
          {n.description && <p>{n.description}</p>}
          {n.skills_matched.length > 0 && <p>Habilidades tuyas que encajan: {n.skills_matched.join(", ")}</p>}
          {n.skills_missing.length > 0 && <p>También se piden: {n.skills_missing.join(", ")}</p>}
        </article>
      ))}
    </>
  );
}