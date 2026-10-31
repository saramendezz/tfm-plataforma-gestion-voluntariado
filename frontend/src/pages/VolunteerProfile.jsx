import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";

const CATEGORY_LABELS = {
  health: "Sanitaria",
  logistics: "Logística y transporte",
  technical: "Técnica y oficios",
  communication: "Comunicación e idiomas",
  social: "Atención y acompañamiento",
  coordination: "Coordinación",
};

export default function VolunteerProfile() {
  const [form, setForm] = useState(null);
  const [skills, setSkills] = useState([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.get("/profiles/volunteer/me/"), api.get("/skills/")])
      .then(([profile, skillList]) => {
        setForm(profile.data);
        setSkills(skillList.data);
      })
      .catch((err) => setError(errorMessage(err)));
  }, []);

  if (!form) return error ? <p className="error">{error}</p> : <p>Cargando...</p>;

  const grouped = skills.reduce((acc, skill) => {
    (acc[skill.category] ||= []).push(skill);
    return acc;
  }, {});

  function onChange(e) {
    const { name, value, type, checked } = e.target;
    setForm({ ...form, [name]: type === "checkbox" ? checked : value });
  }

  function toggleSkill(id) {
    const has = form.skills.includes(id);
    setForm({
      ...form,
      skills: has ? form.skills.filter((s) => s !== id) : [...form.skills, id],
    });
  }

  async function onSubmit(e) {
    e.preventDefault();
    setMessage("");
    setError("");
    try {
      const { data } = await api.patch("/profiles/volunteer/me/", form);
      setForm(data);
      setMessage("Perfil guardado.");
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <>
      <h1>Mi perfil de voluntario</h1>
      <form onSubmit={onSubmit}>
        <label>
          Municipio
          <input name="municipality" value={form.municipality} onChange={onChange} />
        </label>
        <label>
          Provincia
          <input name="province" value={form.province} onChange={onChange} />
        </label>
        <label>
          Código postal
          <input name="postal_code" value={form.postal_code} onChange={onChange} maxLength={5} />
        </label>
        <label>
          Teléfono
          <input name="phone" value={form.phone} onChange={onChange} />
        </label>
        <label>
          Distancia máxima de desplazamiento (km)
          <input name="max_distance_km" type="number" min="1" max="500" value={form.max_distance_km} onChange={onChange} />
        </label>
        <label className="inline">
          <input name="is_available" type="checkbox" checked={form.is_available} onChange={onChange} />
          Estoy disponible para participar
        </label>

        <h2>Habilidades</h2>
        {Object.entries(grouped).map(([category, list]) => (
          <fieldset key={category}>
            <legend>{CATEGORY_LABELS[category] ?? category}</legend>
            {list.map((skill) => (
              <label key={skill.id} className="inline">
                <input
                  type="checkbox"
                  checked={form.skills.includes(skill.id)}
                  onChange={() => toggleSkill(skill.id)}
                />
                {skill.name}
              </label>
            ))}
          </fieldset>
        ))}

        {error && <p className="error">{error}</p>}
        {message && <p className="ok">{message}</p>}
        <button type="submit">Guardar</button>
      </form>
    </>
  );
}