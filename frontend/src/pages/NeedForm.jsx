import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import api, { errorMessage } from "../api";
import { toApiValue, toInputValue } from "../dates";
import SkillPicker from "../SkillPicker";

const EMPTY = {
  title: "",
  description: "",
  municipality: "",
  province: "",
  postal_code: "",
  start_at: "",
  end_at: "",
  volunteers_needed: 1,
  required_skills: [],
  status: "open",
};

export default function NeedForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState(id ? null : EMPTY);
  const [skills, setSkills] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const requests = [api.get("/skills/")];
    if (id) requests.push(api.get(`/needs/${id}/`));
    Promise.all(requests)
      .then(([skillList, need]) => {
        setSkills(skillList.data);
        if (need) {
          setForm({
            ...need.data,
            start_at: toInputValue(need.data.start_at),
            end_at: toInputValue(need.data.end_at),
          });
        }
      })
      .catch((err) => setError(errorMessage(err)));
  }, [id]);

  if (!form) return error ? <p className="error">{error}</p> : <p>Cargando...</p>;

  const closed = form.status === "closed";
  const confirmed = form.confirmed_count ?? 0;
  const locked = confirmed > 0;
  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    const body = {
      title: form.title,
      description: form.description,
      municipality: form.municipality,
      province: form.province,
      postal_code: form.postal_code,
      start_at: toApiValue(form.start_at),
      end_at: toApiValue(form.end_at),
      volunteers_needed: Number(form.volunteers_needed),
      required_skills: form.required_skills,
    };
    try {
      if (id) await api.patch(`/needs/${id}/`, body);
      else await api.post("/needs/", body);
      navigate("/necesidades");
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <>
      <h1>{id ? "Editar necesidad" : "Nueva necesidad"}</h1>
      {closed && <p className="error">Esta necesidad está cerrada y no se puede modificar.</p>}
      {locked && !closed && (
        <p className="hint">
          Hay {confirmed} voluntario(s) apuntado(s): no se pueden cambiar las fechas, el lugar ni
          las habilidades, ni reducir las plazas por debajo de esa cifra.
        </p>
      )}
      <form onSubmit={onSubmit}>
        <fieldset className="plain" disabled={closed}>
          <label>
            Título
            <input name="title" value={form.title} onChange={onChange} maxLength={120} required />
          </label>
          <label>
            Descripción
            <textarea name="description" value={form.description} onChange={onChange} maxLength={500} rows={3} />
          </label>
          <label>
            Municipio
            <input name="municipality" value={form.municipality} onChange={onChange} disabled={locked} required />
          </label>
          <label>
            Provincia
            <input name="province" value={form.province} onChange={onChange} disabled={locked} required />
          </label>
          <label>
            Código postal
            <input name="postal_code" value={form.postal_code} onChange={onChange} maxLength={5} disabled={locked} required />
          </label>
          <label>
            Inicio
            <input name="start_at" type="datetime-local" value={form.start_at} onChange={onChange} disabled={locked} required />
          </label>
          <label>
            Fin
            <input name="end_at" type="datetime-local" value={form.end_at} onChange={onChange} disabled={locked} required />
          </label>
          <label>
            Voluntarios necesarios
            <input name="volunteers_needed" type="number" min={Math.max(1, confirmed)} value={form.volunteers_needed} onChange={onChange} required />
          </label>

          <h2>Habilidades requeridas</h2>
          <SkillPicker
            skills={skills}
            value={form.required_skills}
            onChange={(required_skills) => setForm({ ...form, required_skills })}
            disabled={locked}
          />
        </fieldset>

        {error && <p className="error">{error}</p>}
        {!closed && <button type="submit">Guardar</button>}
      </form>
    </>
  );
}