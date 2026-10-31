import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { errorMessage } from "../api";
import { useAuth } from "../AuthContext";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    role: "volunteer",
  });
  const [error, setError] = useState("");

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      await register(form);
      navigate("/");
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  return (
    <>
      <h1>Crear cuenta</h1>
      <form onSubmit={onSubmit}>
        <label>
          Usuario
          <input name="username" value={form.username} onChange={onChange} required />
        </label>
        <label>
          Email
          <input name="email" type="email" value={form.email} onChange={onChange} required />
        </label>
        <label>
          Contraseña
          <input name="password" type="password" value={form.password} onChange={onChange} required />
        </label>
        <label>
          Quiero registrarme como
          <select name="role" value={form.role} onChange={onChange}>
            <option value="volunteer">Voluntario</option>
            <option value="organization">Organización</option>
          </select>
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit">Crear cuenta</button>
      </form>
      <p>
        ¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link>
      </p>
    </>
  );
}