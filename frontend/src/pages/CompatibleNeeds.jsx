import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";
import { formatDateTime } from "../dates";
import useTitle from "../useTitle";

function scoreLevel(score) {
  if (score >= 75) return { key: "high", label: "Compatibilidad alta" };
  if (score >= 50) return { key: "mid", label: "Compatibilidad media" };
  return { key: "low", label: "Compatibilidad baja" };
}

export default function CompatibleNeeds() {
  useTitle("Necesidades para mí");
  const [needs, setNeeds] = useState(null);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);
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
    setBusyId(need.id);
    try {
      await api.post(`/needs/${need.id}/accept/`);
    } catch (err) {
      setError(errorMessage(err));
    }
    setBusyId(null);
    setReloadKey((k) => k + 1);
  }

  async function leave(need) {
    if (!window.confirm(`¿Retirarte de «${need.title}»? Se liberará tu plaza.`)) return;
    setError("");
    setBusyId(need.id);
    try {
      await api.post(`/participations/${need.participation_id}/withdraw/`);
    } catch (err) {
      setError(errorMessage(err));
    }
    setBusyId(null);
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

      {error && <p className="error" role="alert">{error}</p>}
      {needs === null && <p className="muted">Cargando…</p>}
      {needs && needs.length === 0 && !error && (
        <p className="empty">
          Ahora mismo no hay necesidades compatibles. Comprueba que tu perfil tiene código postal
          y habilidades, que has indicado tu disponibilidad y que tu distancia máxima es suficiente.
        </p>
      )}

      {needs?.map((n) => {
        const score = Number(n.score);
        const level = scoreLevel(score);
        const joined = Boolean(n.participation_id);
        const full = !joined && n.spots_left <= 0;
        return (
          <article key={n.id} className="card need">
            <div className="need-head">
              <h2>{n.title}</h2>
              {joined && <span className="badge confirmed">Ya participas</span>}
            </div>

            <div className="scorebox">
              <div className="scorelabel">
                <span>{level.label}</span>
                <strong>{Math.round(score)} / 100</strong>
              </div>
              <div
                className={`scorebar ${level.key}`}
                role="progressbar"
                aria-label="Puntuación de compatibilidad"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={Math.round(score)}
              >
                <span style={{ width: `${Math.max(0, Math.min(100, score))}%` }} />
              </div>
            </div>

            <ul className="meta">
              <li><span>Organización</span>{n.organization_name}</li>
              <li><span>Lugar</span>{n.municipality} ({n.province}) · a {n.distance_km} km</li>
              <li><span>Cuándo</span>{formatDateTime(n.start_at)} → {formatDateTime(n.end_at)}</li>
              <li>
                <span>Plazas</span>
                {n.spots_left <= 0 ? "Completas" : `Quedan ${n.spots_left} de ${n.volunteers_needed}`}
              </li>
            </ul>

            {n.description && <p>{n.description}</p>}

            {(n.skills_matched.length > 0 || n.skills_missing.length > 0) && (
              <div className="skills">
                {n.skills_matched.length > 0 && (
                  <p>
                    <span className="skills-title">Tus habilidades que encajan</span>
                    <span className="chips">
                      {n.skills_matched.map((s) => (
                        <span key={s} className="chip match">{s}</span>
                      ))}
                    </span>
                  </p>
                )}
                {n.skills_missing.length > 0 && (
                  <p>
                    <span className="skills-title">También se piden</span>
                    <span className="chips">
                      {n.skills_missing.map((s) => (
                        <span key={s} className="chip missing">{s}</span>
                      ))}
                    </span>
                  </p>
                )}
              </div>
            )}

            <div className="actions">
              {joined ? (
                <button className="danger" disabled={busyId === n.id} onClick={() => leave(n)}>
                  Retirarme
                </button>
              ) : (
                <button disabled={full || busyId === n.id} onClick={() => join(n)}>
                  {full ? "Sin plazas" : "Apuntarme"}
                </button>
              )}
            </div>
          </article>
        );
      })}
    </>
  );
}