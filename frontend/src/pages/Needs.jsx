import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errorMessage } from "../api";
import { formatDateTime } from "../dates";

const STATUS_LABELS = { open: "Abierta", closed: "Cerrada" };

export default function Needs() {
  const [needs, setNeeds] = useState(null);
  const [status, setStatus] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    api
      .get("/needs/", { params: status ? { status } : {} })
      .then((r) => {
        if (cancelled) return;
        setNeeds(r.data);
        setError("");
      })
      .catch((err) => {
        if (cancelled) return;
        setNeeds([]);
        setError(errorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, [status, reloadKey]);

  async function closeNeed(need) {
    if (!window.confirm(`¿Cerrar la necesidad «${need.title}»? Ya no se podrá modificar.`)) return;
    try {
      await api.post(`/needs/${need.id}/close/`);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <>
      <h1>Mis necesidades</h1>
      <div className="filters">
        <label className="inline">
          Estado
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Todas</option>
            <option value="open">Abiertas</option>
            <option value="closed">Cerradas</option>
          </select>
        </label>
        <Link className="button" to="/necesidades/nueva">
          Nueva necesidad
        </Link>
      </div>

      {error && <p className="error">{error}</p>}
      {needs === null && <p>Cargando...</p>}
      {needs && needs.length === 0 && !error && <p>No hay necesidades.</p>}

      {needs?.map((need) => (
        <article key={need.id} className="card">
          <h2>
            {need.title} <span className={`badge ${need.status}`}>{STATUS_LABELS[need.status]}</span>
          </h2>
          <p>
            {need.municipality} ({need.province}) · {formatDateTime(need.start_at)} →{" "}
            {formatDateTime(need.end_at)}
          </p>
          <p>
            Han aceptado: {need.confirmed_count} de {need.volunteers_needed}
          </p>
          <div className="actions">
            <Link className="button" to={`/necesidades/${need.id}/voluntarios`}>
              Voluntarios
            </Link>
            {need.status === "open" && (
              <>
                <Link className="button" to={`/necesidades/${need.id}`}>
                  Editar
                </Link>
                <button onClick={() => closeNeed(need)}>Cerrar</button>
              </>
            )}
          </div>
        </article>
      ))}
    </>
  );
}