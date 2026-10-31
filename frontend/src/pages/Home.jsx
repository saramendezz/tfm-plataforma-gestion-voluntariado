import { Navigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function Home() {
  const { user } = useAuth();

  if (user.role === "volunteer") return <Navigate to="/perfil-voluntario" replace />;
  if (user.role === "organization") return <Navigate to="/perfil-organizacion" replace />;

  return (
    <>
      <h1>Administración</h1>
      <p>
        La gestión de usuarios y del catálogo de habilidades se realiza en el{" "}
        <a href="http://localhost:8000/admin/">panel de administración</a>.
      </p>
    </>
  );
}