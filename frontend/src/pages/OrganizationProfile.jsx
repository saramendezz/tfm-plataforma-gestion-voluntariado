import { useEffect, useState } from "react";
import api, { errorMessage } from "../api";

export default function OrganizationProfile() {
  const [form, setForm] = useState(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/profiles/organization/me/")
      .then((r) => setForm(r.data))
      .catch((err) => setError(errorMessage(err)));
  }, []);

  if (!form) return error ? <p className="error">{error}</p> : <p>Cargando...</p>;

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  async function onSubmit(e) {
    e.preventDefault();
    setMessage("");
    setError("");
    try {
      const { data } = await api.patch("/profiles/organization/me/", form);
      setForm(data);
      setMessage("Perfil guardado.");
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <>
      <h1>Mi organización</h1>
      <p>
        Estado:{" "}
        {form.is_verified ? "verificada" : "pendiente de verificación por un administrador"}
      </p>
      <form onSubmit={onSubmit}>
        <label>
          Nombre
          <input name="name" value={form.name} onChange={onChange} />
        </label>
        <label>
          Descripción
          <textarea name="description" value={form.description} onChange={onChange} maxLength={500} rows={4} />
        </label>
        <label>
          Teléfono
          <input name="phone" value={form.phone} onChange={onChange} />
        </label>
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
        {error && <p className="error">{error}</p>}
        {message && <p className="ok">{message}</p>}
        <button type="submit">Guardar</button>
      </form>
    </>
  );
}