import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";
import { formatDateTime, toApiValue } from "../dates";

export default function Availability() {
  const [slots, setSlots] = useState(null);
  const [form, setForm] = useState({ start_at: "", end_at: "" });
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    api
      .get("/availability/")
      .then((r) => {
        if (!cancelled) setSlots(r.data);
      })
      .catch((err) => {
        if (cancelled) return;
        setSlots([]);
        setError(errorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      await api.post("/availability/", {
        start_at: toApiValue(form.start_at),
        end_at: toApiValue(form.end_at),
      });
      setForm({ start_at: "", end_at: "" });
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function remove(slot) {
    if (!window.confirm("¿Eliminar esta franja?")) return;
    setError("");
    try {
      await api.delete(`/availability/${slot.id}/`);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <>
      <h1>Mi disponibilidad</h1>
      <p>Indica las franjas de fecha y hora en las que puedes colaborar.</p>

      <form onSubmit={onSubmit}>
        <label>
          Desde
          <input name="start_at" type="datetime-local" value={form.start_at} onChange={onChange} required />
        </label>
        <label>
          Hasta
          <input name="end_at" type="datetime-local" value={form.end_at} onChange={onChange} required />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit">Añadir franja</button>
      </form>

      <h2>Franjas indicadas</h2>
      {slots === null && <p>Cargando...</p>}
      {slots && slots.length === 0 && <p>Todavía no has indicado ninguna franja.</p>}
      {slots?.map((slot) => (
        <article key={slot.id} className="card">
          <p>
            {formatDateTime(slot.start_at)} → {formatDateTime(slot.end_at)}
          </p>
          <div className="actions">
            <button onClick={() => remove(slot)}>Eliminar</button>
          </div>
        </article>
      ))}
    </>
  );
}