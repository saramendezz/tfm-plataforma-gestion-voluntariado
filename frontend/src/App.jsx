import { useEffect, useState } from "react";
import axios from "axios";

export default function App() {
  const [estado, setEstado] = useState("comprobando...");

  useEffect(() => {
    axios
      .get("http://localhost:8000/api/health/")
      .then((r) => setEstado(r.data.status))
      .catch(() => setEstado("error de conexión"));
  }, []);

  return <h1>Backend: {estado}</h1>;
}