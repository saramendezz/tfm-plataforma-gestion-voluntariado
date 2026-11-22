import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import api, { errorMessage } from "../api";
import { formatDateTime } from "../dates";

export default function Candidates() {
  const { id } = useParams();
  const [need, setNeed] = useState(null);
  const [candidates, setCandidates] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.get(`/needs/${id}/`), api.get(`/needs/${id}/candidates/`)])
      .then(([needResponse, candidatesResponse]) => {
        if (cancelled) return;
        setNeed(needResponse.data);
        setCandidates(candidatesResponse.data);
      })
      .catch((err) => {
        if (!cancelled) setError(errorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (error) {
    return (
      <>
        <p className="error">{error}</p>
        <Link to="/necesidades">Volver a mis necesidades</Link>
      </>
    );
  }
  if (!need || !candidates) return <p>Cargando...</p>;

  const hasSkills = need.required_skills.length > 0;

  return (
    <>
      <p>
        <Link to="/necesidades">← Mis necesidades</Link>
      </p>
      <h1>Candidatos</h1>
      <p>
        <strong>{need.title}</strong> · {need.municipality} ({need.province}) ·{" "}
        {formatDateTime(need.start_at)} → {formatDateTime(need.end_at)}
      </p>
      <p>Voluntarios necesarios: {need.volunteers_needed}</p>
      <p className="hint">
        Aparecen las personas disponibles durante todo el horario, con al menos una de las
        habilidades requeridas (si las hay) y dentro de su distancia máxima de desplazamiento.
        La puntuación (0 a 100) pondera habilidades y cercanía. Son sugerencias: la decisión
        corresponde a la organización.
      </p>

      {candidates.length === 0 && <p>No hay candidatos compatibles con esta necesidad.</p>}

      {candidates.map((c) => (
        <article key={c.volunteer_id} className="card">
          <h2>
            {c.username} <span className="score">{c.score}</span>
          </h2>
          <p>
            {c.municipality} ({c.province}) · a {c.distance_km} km
          </p>
          {hasSkills && (
            <p>Cubre: {c.skills_matched.length ? c.skills_matched.join(", ") : "ninguna"}</p>
          )}
          {c.skills_missing.length > 0 && <p>Le falta: {c.skills_missing.join(", ")}</p>}
        </article>
      ))}
    </>
  );
}