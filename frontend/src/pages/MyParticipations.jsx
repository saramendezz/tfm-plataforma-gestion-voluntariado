import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";
import { formatDateTime } from "../dates";

const STATUS_LABELS = {
  confirmed: "Confirmada",
  withdrawn: "Retirada por ti",
  removed: "Retirada por la organización",
};

export default function MyParticipations() {
  const [items, setItems] = useState(null);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    api
      .get("/participations/")
      .then((r) => {
        if (!cancelled) setItems(r.data);
      })
      .catch((err) => {
        if (cancelled) return;
        setItems([]);
        setError(errorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  async function withdraw(item) {
    if (!window.confirm(`¿Retirarte de «${item.need.title}»? Se liberará tu plaza.`)) return;
    setError("");
    try {
      await api.post(`/participations/${item.id}/withdraw/`);
    } catch (err) {
      setError(errorMessage(err));
    }
    setReloadKey((k) => k + 1);
  }

  return (
    <>
      <h1>Mis participaciones</h1>
      {error && <p className="error">{error}</p>}
      {items === null && <p>Cargando...</p>}
      {items && items.length === 0 && !error && <p>Todavía no te has apuntado a ninguna necesidad.</p>}

      {items?.map((item) => (
        <article key={item.id} className="card">
          <h2>
            {item.need.title} <span className={`badge ${item.status}`}>{STATUS_LABELS[item.status]}</span>
          </h2>
          <p>
            {item.need.organization_name} · {item.need.municipality} ({item.need.province})
          </p>
          <p>
            {formatDateTime(item.need.start_at)} → {formatDateTime(item.need.end_at)}
          </p>
          <p>Te apuntaste el {formatDateTime(item.accepted_at)}</p>
          {item.can_withdraw && (
            <div className="actions">
              <button className="danger" onClick={() => withdraw(item)}>
                Retirarme
              </button>
            </div>
          )}
        </article>
      ))}
    </>
  );
}