import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";
import { formatDateTime } from "../dates";

export default function CompatibleNeeds() {
  const [needs, setNeeds] = useState(null);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

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
  }, [reloadKey]);

  async function join(need) {
    const ok = window.confirm(
      `Al apuntarte a «${need.title}», ${need.organization_name} podrá ver tu nombre de usuario, ` +
        "tu email y tu teléfono. ¿Quieres continuar?"
    );
    if (!ok) return;
    setError("");
    try {
      await api.post(`/needs/${need.id}/accept/`);
    } catch (err) {
      setError(errorMessage(err));
    }
    setReloadKey((k) => k + 1);
  }

  async function leave(need) {
    if (!window.confirm(`¿Retirarte de «${need.title}»? Se liberará tu plaza.`)) return;
    setError("");
    try {
      await api.post(`/participations/${need.participation_id}/withdraw/`);
    } catch (err) {
      setError(errorMessage(err));
    }
    setReloadKey((k) => k + 1);
  }

  return (
    <>
      <h1>Necesidades para mí</h1>
      <p className="hint">
        Necesidades abiertas que encajan con tu disponibilidad, tus habilidades y tu distancia
        máxima de desplazamiento, ordenadas de mayor a menor compatibilidad. Tú decides si te
        apuntas: tus datos de contacto solo se muestran a la organización si aceptas.
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
            {n.participation_id && <span className="badge confirmed">Ya participas</span>}
          </h2>
          <p>
            {n.organization_name} · {n.municipality} ({n.province}) · a {n.distance_km} km
          </p>
          <p>
            {formatDateTime(n.start_at)} → {formatDateTime(n.end_at)} · Plazas libres: {n.spots_left} de{" "}
            {n.volunteers_needed}
          </p>
          {n.description && <p>{n.description}</p>}
          {n.skills_matched.length > 0 && <p>Habilidades tuyas que encajan: {n.skills_matched.join(", ")}</p>}
          {n.skills_missing.length > 0 && <p>También se piden: {n.skills_missing.join(", ")}</p>}
          <div className="actions">
            {n.participation_id ? (
              <button className="danger" onClick={() => leave(n)}>
                Retirarme
              </button>
            ) : (
              <button onClick={() => join(n)}>Apuntarme</button>
            )}
          </div>
        </article>
      ))}
    </>
  );
}