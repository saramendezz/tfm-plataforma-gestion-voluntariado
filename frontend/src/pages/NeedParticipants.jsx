import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import api, { errorMessage } from "../api";
import { formatDateTime } from "../dates";

export default function NeedParticipants() {
  const { id } = useParams();
  const [need, setNeed] = useState(null);
  const [potential, setPotential] = useState(null);
  const [participants, setParticipants] = useState(null);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      api.get(`/needs/${id}/`),
      api.get(`/needs/${id}/potential/`),
      api.get(`/needs/${id}/participants/`),
    ])
      .then(([needResponse, potentialResponse, participantsResponse]) => {
        if (cancelled) return;
        setNeed(needResponse.data);
        setPotential(potentialResponse.data);
        setParticipants(participantsResponse.data);
      })
      .catch((err) => {
        if (!cancelled) setError(errorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, [id, reloadKey]);

  async function remove(p) {
    if (!window.confirm(`¿Retirar a ${p.username}? No podrá volver a apuntarse a esta necesidad.`)) return;
    setError("");
    try {
      await api.post(`/participations/${p.participation_id}/remove/`);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  if (!need || !participants || !potential) {
    return (
      <>
        {error ? <p className="error">{error}</p> : <p>Cargando...</p>}
        <Link to="/necesidades">Volver a mis necesidades</Link>
      </>
    );
  }

  return (
    <>
      <p>
        <Link to="/necesidades">← Mis necesidades</Link>
      </p>
      <h1>Voluntarios</h1>
      <p>
        <strong>{need.title}</strong> · {need.municipality} ({need.province}) ·{" "}
        {formatDateTime(need.start_at)} → {formatDateTime(need.end_at)}
      </p>
      <p>
        Han aceptado: <strong>{participants.length}</strong> de {need.volunteers_needed}. Voluntarios
        compatibles en la plataforma: <strong>{potential.potential_volunteers}</strong>.
      </p>
      <p className="hint">
        Los voluntarios deciden por sí mismos si se apuntan. Solo ves la identidad y el contacto de
        quienes han aceptado; del resto únicamente el número.
      </p>

      {error && <p className="error">{error}</p>}
      {participants.length === 0 && <p>Todavía no ha aceptado ningún voluntario.</p>}

      {participants.map((p) => (
        <article key={p.participation_id} className="card">
          <h2>{p.username}</h2>
          <p>
            {p.email} · {p.phone || "teléfono no indicado"}
          </p>
          <p>
            {p.municipality} ({p.province}) · aceptó el {formatDateTime(p.accepted_at)}
          </p>
          {p.skills.length > 0 && <p>Habilidades: {p.skills.join(", ")}</p>}
          <div className="actions">
            <button className="danger" onClick={() => remove(p)}>
              Retirar
            </button>
          </div>
        </article>
      ))}
    </>
  );
}